// Malformed SSE detection via fetch monkey-patch.
// Intercepts Datastar SSE requests, tees the response stream, validates one
// copy while Datastar consumes the other. Zero Datastar patches needed.

export interface SSEValidationError {
  level: "warning" | "error";
  code: string;
  message: string;
  rawText: string;
  url: string;
  byteOffset: number;
}

type SSEValidationCallback = (error: SSEValidationError) => void;
type Emit = (level: SSEValidationError["level"], code: string, message: string) => void;

const MAX_BYTES_PER_RESPONSE = 1_048_576; // 1MB safety valve
const RAW_TEXT_MAX = 200;

const DATASTAR_EVENT_TYPES = new Set([
  "datastar-patch-signals",
  "datastar-patch-elements",
  "datastar-execute-script",
]);

const VALID_SSE_FIELDS = new Set(["event", "data", "id", "retry"]);

const VALID_ELEMENT_MODES = new Set([
  "outer",
  "inner",
  "replace",
  "prepend",
  "append",
  "before",
  "after",
  "remove",
]);

// biome-ignore lint/suspicious/noControlCharactersInRegex: intentional binary/control char detection
const CONTROL_CHAR_RE = /[\x00-\x08\x0B\x0E-\x1F\x7F]/;

let originalFetch: typeof window.fetch | null = null;
let activeCallback: SSEValidationCallback | null = null;
const encoder = new TextEncoder();

export function install(callback: SSEValidationCallback): void {
  if (originalFetch) return; // already installed
  activeCallback = callback;
  originalFetch = window.fetch;
  window.fetch = interceptedFetch as typeof window.fetch;
}

export function uninstall(): void {
  if (originalFetch) {
    window.fetch = originalFetch;
    originalFetch = null;
  }
  activeCallback = null;
}

function isDatastarHeaders(headers: HeadersInit): boolean {
  const h = new Headers(headers);
  return h.has("Datastar-Request") || h.get("Accept") === "text/event-stream";
}

function isDatastarSSERequest(input: RequestInfo | URL, init?: RequestInit): boolean {
  // init headers override Request headers per fetch spec
  if (init?.headers && isDatastarHeaders(init.headers)) return true;
  if (input instanceof Request && isDatastarHeaders(input.headers)) return true;
  return false;
}

async function interceptedFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  if (!originalFetch) return window.fetch(input, init);
  if (!isDatastarSSERequest(input, init)) return originalFetch(input, init);

  const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
  // Network errors propagate to caller — not an SSE validation issue
  const response = await originalFetch(input, init);

  const ct = response.headers.get("Content-Type") ?? "";
  if (!ct.includes("text/event-stream")) {
    emitError({
      level: "error",
      code: "WRONG_CONTENT_TYPE",
      message: `Expected text/event-stream, got: ${ct}`,
      rawText: "",
      url,
      byteOffset: 0,
    });
  }

  if (!response.body) return response;

  const [datastarCopy, validatorCopy] = response.body.tee();

  // Fire and forget — validation runs alongside Datastar consumption
  validateStream(validatorCopy, url).catch(() => {});

  const proxied = new Response(datastarCopy, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
  for (const prop of ["url", "type", "redirected"] as const) {
    Object.defineProperty(proxied, prop, { value: response[prop] });
  }
  return proxied;
}

async function validateStream(stream: ReadableStream<Uint8Array>, url: string): Promise<void> {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let totalBytes = 0;
  let byteOffset = 0;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      totalBytes += value.byteLength;
      if (totalBytes > MAX_BYTES_PER_RESPONSE) {
        await reader.cancel();
        break;
      }

      // SSE spec: CR, LF, and CRLF are all valid line endings
      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk.replace(/\r\n?/g, "\n");

      while (true) {
        const blankIdx = buffer.indexOf("\n\n");
        if (blankIdx === -1) break;
        const rawEvent = buffer.slice(0, blankIdx);
        buffer = buffer.slice(blankIdx + 2);
        if (rawEvent.trim()) {
          validateRawEvent(rawEvent, url, byteOffset);
        }
        byteOffset += encoder.encode(rawEvent).byteLength + 2;
      }
    }

    const remaining = buffer.trim();
    if (remaining) {
      emitError({
        level: "warning",
        code: "MISSING_TRAILING_BLANK_LINE",
        message: "Stream ended without trailing blank line after last event",
        rawText: remaining.slice(0, RAW_TEXT_MAX),
        url,
        byteOffset,
      });
      validateRawEvent(remaining, url, byteOffset);
    }
  } catch (err) {
    emitError({
      level: "error",
      code: "STREAM_ERROR",
      message: `Stream read failed: ${err instanceof Error ? err.message : String(err)}`,
      rawText: "",
      url,
      byteOffset,
    });
  } finally {
    try {
      reader.releaseLock();
    } catch {
      /* noop */
    }
  }
}

function validateRawEvent(raw: string, url: string, byteOffset: number): void {
  const lines = raw.split("\n");
  let eventType: string | null = null;
  let eventTypeCount = 0;
  const dataLines: string[] = [];
  const rawText = raw.slice(0, RAW_TEXT_MAX);
  const emit: Emit = (level, code, message) =>
    emitError({ level, code, message, rawText, url, byteOffset });

  for (const line of lines) {
    if (line.startsWith(":")) continue;

    const colonIdx = line.indexOf(":");
    if (colonIdx === -1) continue; // Bare field name per SSE spec — ignored

    const field = line.slice(0, colonIdx);
    const value = line.slice(colonIdx + 1).trimStart();

    if (!VALID_SSE_FIELDS.has(field)) {
      emit("warning", "UNKNOWN_FIELD", `Unknown SSE field: "${field}"`);
    }

    if (field === "event") {
      eventType = value;
      eventTypeCount++;
    } else if (field === "data") {
      dataLines.push(value);
      if (CONTROL_CHAR_RE.test(value)) {
        emit("error", "BINARY_DATA", "Data line contains binary/control characters");
      }
    }
  }

  if (eventTypeCount > 1) {
    emit(
      "error",
      "MERGED_EVENTS",
      `Found ${eventTypeCount} event: lines in one block — missing blank line separator`
    );
    return;
  }

  if (!eventType && dataLines.length > 0) {
    emit("error", "MISSING_EVENT_TYPE", "Event has data lines but no event: type line");
    return;
  }

  if (!eventType) return;

  if (!DATASTAR_EVENT_TYPES.has(eventType)) {
    emit("warning", "NON_DATASTAR_EVENT", `Unknown event type: "${eventType}"`);
    return;
  }

  if (eventType === "datastar-patch-signals") {
    validateSignalsData(dataLines, emit);
  } else if (eventType === "datastar-patch-elements") {
    validateElementsData(dataLines, emit);
  }
}

function validateSignalsData(dataLines: string[], emit: Emit): void {
  let hasSignals = false;
  for (const line of dataLines) {
    if (line.startsWith("signals ")) {
      hasSignals = true;
      const json = line.slice("signals ".length);
      try {
        const parsed = JSON.parse(json);
        if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
          emit("error", "INVALID_SIGNALS_JSON", "Signals data must be a JSON object");
        }
      } catch {
        emit("error", "INVALID_SIGNALS_JSON", `Invalid JSON in signals data: ${json.slice(0, 80)}`);
      }
    }
  }
  if (!hasSignals) {
    emit(
      "error",
      "MISSING_SIGNALS_DATA",
      "datastar-patch-signals event missing 'signals' data key"
    );
  }
}

function validateElementsData(dataLines: string[], emit: Emit): void {
  let hasElements = false;
  let elementContent = "";
  for (const line of dataLines) {
    if (line.startsWith("elements ")) {
      hasElements = true;
      elementContent += line.slice("elements ".length);
    } else if (line.startsWith("mode ")) {
      const mode = line.slice("mode ".length).trim();
      if (!VALID_ELEMENT_MODES.has(mode)) {
        emit(
          "error",
          "INVALID_ELEMENT_MODE",
          `Invalid mode: "${mode}". Valid: ${[...VALID_ELEMENT_MODES].join(", ")}`
        );
      }
    }
  }
  if (!hasElements) {
    emit(
      "error",
      "MISSING_ELEMENTS_DATA",
      "datastar-patch-elements event missing 'elements' data key"
    );
  } else if (!elementContent.trim()) {
    emit("warning", "EMPTY_FRAGMENT", "Elements event has empty fragment content");
  }
}

function emitError(error: SSEValidationError): void {
  if (activeCallback) activeCallback(error);
}
