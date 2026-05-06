#!/usr/bin/env python3
"""Verify that all Datastar patches are applied to the built core file."""

import sys
from pathlib import Path

DATASTAR_PATH = Path(__file__).resolve().parent.parent / "src" / "starhtml" / "static" / "js" / "datastar-core.js"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from patch_definitions import verify  # noqa: E402


def main() -> int:
    if not DATASTAR_PATH.exists():
        print(f"FAIL: {DATASTAR_PATH} not found")
        return 1

    content = DATASTAR_PATH.read_text()
    results = verify(content)
    ok = True

    for label, detail, passed in results:
        if passed:
            print(f"  PASS: {label}")
        else:
            print(f"  FAIL: {label} — {detail}")
            ok = False

    print("\nAll patches verified." if ok else "\nSome patches are missing!")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
