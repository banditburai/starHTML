// debugger-sse-validator.ts — Malformed SSE detection via fetch monkey-patch.
// Intercepts Datastar SSE requests, tees the response stream, validates one
// copy while Datastar consumes the other. Zero Datastar patches needed.

// ─── Interfaces ────────────────────────────────────────────────────

export interface SSEValidationError {
  level: "warning" | "error";
  code: string;
  message: string;
  rawText: string;
  url: string;
  byteOffset: number;
}

export type SSEValidationCallback = (error: SSEValidationError) => void;

// ─── Constants ─────────────────────────────────────────────────────

const MAX_BYTES_PER_RESPONSE = 1_048_576; // 1MB safety valve
const RAW_TEXT_MAX = 200;

const DATASTAR_EVENT_TYPES = new Set([
  "datastar-patch-signals",
  "datastar-patch-elements",
  "datastar-execute-script",
]);

const VALID_SSE_FIELDS = new Set([
  "event", "data", "id", "retry",
]);

const VALID_ELEMENT_MODES = new Set([
  "outer", "inner", "replace", "prepend", "append", "before", "after", "remove",
]);

// ─── State ─────────────────────────────────────────────────────────

let originalFetch: typeof window.fetch | null = null;
let activeCallback: SSEValidationCallback | null = null;

// ─── Public API ────────────────────────────────────────────────────

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

// ─── Fetch interceptor ─────────────────────────────────────────────

function isDatastarSSERequest(input: RequestInfo | URL, init?: RequestInit): boolean {
  const headers = init?.headers;
  if (headers) {
    if (headers instanceof Headers) {
      if (headers.has("Datastar-Request")) return true;
      if (headers.get("Accept") === "text/event-stream") return true;
    } else if (Array.isArray(headers)) {
      for (const [k, v] of headers) {
        if (k === "Datastar-Request") return true;
        if (k === "Accept" && v === "text/event-stream") return true;
      }
    } else {
      if ("Datastar-Request" in headers) return true;
      if ((headers as Record<string, string>)["Accept"] === "text/event-stream") return true;
    }
  }
  return false;
}

function getRequestUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") return input;
  if (input instanceof URL) return input.href;
  return input.url;
}

async function interceptedFetch(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  if (!isDatastarSSERequest(input, init) || !originalFetch) {
    return originalFetch!(input, init);
  }

  const url = getRequestUrl(input);
  let response: Response;
  try {
    response = await originalFetch(input, init);
  } catch (err) {
    // Network error — not an SSE validation issue
    throw err;
  }

  // Check content-type
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

  // Tee the body — one copy for Datastar, one for validation
  if (!response.body) return response;

  const [datastarCopy, validatorCopy] = response.body.tee();

  // Start async validation (fire and forget)
  validateStream(validatorCopy, url);

  // Return a new Response with the Datastar copy
  return new Response(datastarCopy, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
}

// ─── Stream validation ─────────────────────────────────────────────

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
        reader.cancel();
        break;
      }

      buffer += decoder.decode(value, { stream: true });

      // Process complete events (separated by blank lines)
      let blankIdx: number;
      while ((blankIdx = buffer.indexOf("\n\n")) !== -1) {
        const rawEvent = buffer.slice(0, blankIdx);
        buffer = buffer.slice(blankIdx + 2);
        if (rawEvent.trim()) {
          validateRawEvent(rawEvent, url, byteOffset);
        }
        byteOffset += new TextEncoder().encode(rawEvent).byteLength + 2;
      }
    }

    // Handle trailing content without final blank line
    const remaining = buffer.trim();
    if (remaining) {
      // Check if it looks like an SSE event without trailing blank line
      if (remaining.includes("event:") || remaining.includes("data:")) {
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
    try { reader.releaseLock(); } catch { /* already released */ }
  }
}

// ─── Raw event validation ──────────────────────────────────────────

function validateRawEvent(raw: string, url: string, byteOffset: number): void {
  const lines = raw.split("\n");
  let eventType: string | null = null;
  let eventTypeCount = 0;
  const dataLines: string[] = [];
  const truncated = raw.slice(0, RAW_TEXT_MAX);

  for (const line of lines) {
    // SSE comment lines
    if (line.startsWith(":")) continue;

    const colonIdx = line.indexOf(":");
    if (colonIdx === -1) continue; // Bare field name per SSE spec — ignored

    const field = line.slice(0, colonIdx);
    const value = line.slice(colonIdx + 1).trimStart();

    // Check for unknown fields
    if (!VALID_SSE_FIELDS.has(field)) {
      emitError({
        level: "warning",
        code: "UNKNOWN_FIELD",
        message: `Unknown SSE field: "${field}"`,
        rawText: truncated,
        url,
        byteOffset,
      });
    }

    if (field === "event") {
      eventType = value;
      eventTypeCount++;
    } else if (field === "data") {
      dataLines.push(value);

      // Check for binary/control characters
      if (/[\x00-\x08\x0B\x0E-\x1F\x7F]/.test(value)) {
        emitError({
          level: "error",
          code: "BINARY_DATA",
          message: "Data line contains binary/control characters",
          rawText: truncated,
          url,
          byteOffset,
        });
      }
    }
  }

  // Merged events: two event: lines in one block
  if (eventTypeCount > 1) {
    emitError({
      level: "error",
      code: "MERGED_EVENTS",
      message: `Found ${eventTypeCount} event: lines in one block — missing blank line separator`,
      rawText: truncated,
      url,
      byteOffset,
    });
    return; // Can't reliably validate merged events
  }

  // Missing event type
  if (!eventType && dataLines.length > 0) {
    emitError({
      level: "error",
      code: "MISSING_EVENT_TYPE",
      message: "Event has data lines but no event: type line",
      rawText: truncated,
      url,
      byteOffset,
    });
    return;
  }

  if (!eventType) return;

  // Non-Datastar event type
  if (!DATASTAR_EVENT_TYPES.has(eventType)) {
    emitError({
      level: "warning",
      code: "NON_DATASTAR_EVENT",
      message: `Unknown event type: "${eventType}"`,
      rawText: truncated,
      url,
      byteOffset,
    });
    return;
  }

  // Per-type validation
  if (eventType === "datastar-patch-signals") {
    validateSignalsData(dataLines, truncated, url, byteOffset);
  } else if (eventType === "datastar-patch-elements") {
    validateElementsData(dataLines, truncated, url, byteOffset);
  }
}

// ─── Per-type validators ───────────────────────────────────────────

function validateSignalsData(dataLines: string[], rawText: string, url: string, byteOffset: number): void {
  let hasSignals = false;
  for (const line of dataLines) {
    if (line.startsWith("signals ")) {
      hasSignals = true;
      const json = line.slice("signals ".length);
      try {
        const parsed = JSON.parse(json);
        if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
          emitError({
            level: "error",
            code: "INVALID_SIGNALS_JSON",
            message: "Signals data must be a JSON object",
            rawText,
            url,
            byteOffset,
          });
        }
      } catch {
        emitError({
          level: "error",
          code: "INVALID_SIGNALS_JSON",
          message: `Invalid JSON in signals data: ${json.slice(0, 80)}`,
          rawText,
          url,
          byteOffset,
        });
      }
    }
  }
  if (!hasSignals) {
    emitError({
      level: "error",
      code: "MISSING_SIGNALS_DATA",
      message: "datastar-patch-signals event missing 'signals' data key",
      rawText,
      url,
      byteOffset,
    });
  }
}

function validateElementsData(dataLines: string[], rawText: string, url: string, byteOffset: number): void {
  let hasElements = false;
  let elementContent = "";
  for (const line of dataLines) {
    if (line.startsWith("elements ")) {
      hasElements = true;
      elementContent += line.slice("elements ".length);
    } else if (line.startsWith("mode ")) {
      const mode = line.slice("mode ".length).trim();
      if (!VALID_ELEMENT_MODES.has(mode)) {
        emitError({
          level: "error",
          code: "INVALID_ELEMENT_MODE",
          message: `Invalid mode: "${mode}". Valid: ${[...VALID_ELEMENT_MODES].join(", ")}`,
          rawText,
          url,
          byteOffset,
        });
      }
    }
  }
  if (!hasElements) {
    emitError({
      level: "error",
      code: "MISSING_ELEMENTS_DATA",
      message: "datastar-patch-elements event missing 'elements' data key",
      rawText,
      url,
      byteOffset,
    });
  } else if (!elementContent.trim()) {
    emitError({
      level: "warning",
      code: "EMPTY_FRAGMENT",
      message: "Elements event has empty fragment content",
      rawText,
      url,
      byteOffset,
    });
  }
}

// ─── Error emission ────────────────────────────────────────────────

function emitError(error: SSEValidationError): void {
  if (activeCallback) activeCallback(error);
}
