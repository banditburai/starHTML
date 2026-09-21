#!/usr/bin/env python3
"""Build StarHTML's Datastar runtime from vanilla upstream source.

Called by `bun run build` (via build.ts) to produce:

- src/starhtml/static/js/datastar-core.js: patched Datastar core.
- src/starhtml/static/js/datastar.js: StarHTML wrapper that prehydrates persisted
  signals through Datastar's public API before Datastar's deferred first scan.

The public import map points at datastar.js. The wrapper imports the private
core module and re-exports its API, so plugins still import from "datastar".
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM_PATH = ROOT / "patches" / "datastar-upstream.js"
OUTPUT_PATH = ROOT / "src" / "starhtml" / "static" / "js" / "datastar.js"
CORE_OUTPUT_PATH = ROOT / "src" / "starhtml" / "static" / "js" / "datastar-core.js"
STARAPP_PATH = ROOT / "src" / "starhtml" / "starapp.py"

sys.path.insert(0, str(ROOT / "patches"))
from patch_definitions import apply_all, verify  # noqa: E402

WRAPPER_TEMPLATE = """// Datastar v{version} (StarHTML wrapper: persist-prehydrate)
import {{ mergePatch }} from "./datastar-core.js";
export * from "./datastar-core.js";

const DEFAULT_STORAGE_PREFIX = "starhtml-persist";

function readPersistedSignals() {{
  const patch = {{}};
  const sources = {{}};

  for (const [storageName, getStorage] of [
    ["local", () => globalThis.localStorage],
    ["session", () => globalThis.sessionStorage],
  ]) {{
    try {{
      const storage = getStorage();
      for (let i = 0; i < storage.length; i++) {{
        const storageKey = storage.key(i);
        if (!storageKey?.startsWith(DEFAULT_STORAGE_PREFIX)) continue;
        try {{
          const data = JSON.parse(storage.getItem(storageKey) || "{{}}");
          if (!data || typeof data !== "object" || Array.isArray(data)) continue;
          for (const [path, value] of Object.entries(data)) {{
            if (value == null) continue;
            patch[path] = value;
            sources[path] = {{ storage: storageName, storageKey }};
          }}
        }} catch {{}}
      }}
    }} catch {{}}
  }}

  return {{ patch, sources }};
}}

const {{ patch, sources }} = readPersistedSignals();
if (Object.keys(patch).length > 0) {{
  globalThis.__starhtml_pc = {{ ...patch }};
  const sourceDetail = {{
    source: "persist",
    signals: patch,
    paths: Object.keys(patch),
    sources,
    phase: "before",
  }};
  (globalThis.__starhtml_signal_sources ||= []).push(sourceDetail);
  document.dispatchEvent(new CustomEvent("starhtml:signal-source", {{ detail: sourceDetail }}));
  mergePatch(patch);
}}
"""


def get_version() -> str:
    """Read DATASTAR_VERSION from starapp.py, stripping +starhtml suffix."""
    content = STARAPP_PATH.read_text()
    match = re.search(r'DATASTAR_VERSION\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        print("ERROR: DATASTAR_VERSION not found in starapp.py")
        sys.exit(1)
    return match.group(1).split("+")[0]


def main() -> int:
    if not UPSTREAM_PATH.exists():
        print(f"ERROR: {UPSTREAM_PATH} not found")
        return 1

    version = get_version()
    vanilla = UPSTREAM_PATH.read_text()
    print(f"Datastar {version}: patching {len(vanilla)} bytes from {UPSTREAM_PATH.name}")

    try:
        patched = apply_all(vanilla, version)
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    results = verify(patched)
    all_pass = all(passed for _, _, passed in results)
    for label, detail, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {label} — {detail}")

    if not all_pass:
        print("ERROR: Verification failed after patching!")
        return 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CORE_OUTPUT_PATH.write_text(patched)

    wrapper = WRAPPER_TEMPLATE.format(version=version)
    OUTPUT_PATH.write_text(wrapper)

    print(f"Wrote {len(patched)} bytes to {CORE_OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Wrote {len(wrapper)} bytes to {OUTPUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
