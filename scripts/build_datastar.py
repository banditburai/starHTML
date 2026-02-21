#!/usr/bin/env python3
"""Build patched datastar.js from vanilla upstream source.

Called by `bun run build` (via build.ts) to produce src/starhtml/static/js/datastar.js
alongside the TypeScript-built plugins and debugger JS.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM_PATH = ROOT / "patches" / "datastar-upstream.js"
OUTPUT_PATH = ROOT / "src" / "starhtml" / "static" / "js" / "datastar.js"
STARAPP_PATH = ROOT / "src" / "starhtml" / "starapp.py"

sys.path.insert(0, str(ROOT / "patches"))
from patch_definitions import apply_all, verify  # noqa: E402


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
    OUTPUT_PATH.write_text(patched)
    print(f"Wrote {len(patched)} bytes to {OUTPUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
