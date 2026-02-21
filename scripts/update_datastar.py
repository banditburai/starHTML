#!/usr/bin/env python3
"""Update vanilla Datastar upstream source: download from CDN, dry-run patches, update version.

After running this, run `bun run build` to apply patches and produce static/js/datastar.js.
"""

import re
import sys
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
STARAPP_PATH = ROOT / "src" / "starhtml" / "starapp.py"
UPSTREAM_PATH = ROOT / "patches" / "datastar-upstream.js"
CDN_URL = "https://cdn.jsdelivr.net/gh/starfederation/datastar@{version}/bundles/datastar.js"

sys.path.insert(0, str(ROOT / "patches"))
from patch_definitions import PATCHES, apply_all, verify  # noqa: E402


def get_current_version() -> str:
    content = STARAPP_PATH.read_text()
    match = re.search(r'DATASTAR_VERSION\s*=\s*["\']([^"\']+)["\']', content)
    return match.group(1) if match else "unknown"


def update_version_constant(new_version: str) -> None:
    content = STARAPP_PATH.read_text()
    updated = re.sub(
        r'(DATASTAR_VERSION\s*=\s*["\'])[^"\']+(["\'])',
        rf"\g<1>{new_version}+starhtml\g<2>",
        content,
    )
    STARAPP_PATH.write_text(updated)


def download_datastar(version: str) -> str:
    url = CDN_URL.format(version=version)
    print(f"Downloading from {url}")
    with urlopen(url) as response:
        return response.read().decode("utf-8")


def main() -> int:
    current = get_current_version()
    print(f"Current version: {current}")

    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <version>")
        print(f"Example: {sys.argv[0]} 1.0.0-RC.8")
        return 1

    new_version = sys.argv[1].lstrip("v")
    print(f"Updating to: {new_version}")

    vanilla = download_datastar(new_version)
    print(f"Downloaded {len(vanilla)} bytes")

    # Dry-run: verify patches can be applied to the new version
    try:
        patched = apply_all(vanilla, new_version)
        print(f"Dry-run: applied {len(PATCHES)} patches ({len(patched)} bytes)")
    except ValueError as e:
        print(f"\nERROR: {e}")
        print("\nThe Datastar internals may have changed.")
        print("Fix the search strings in patches/patch_definitions.py")
        vanilla_path = UPSTREAM_PATH.with_suffix(".vanilla.js")
        vanilla_path.write_text(vanilla)
        print(f"Vanilla file saved to: {vanilla_path}")
        return 1

    results = verify(patched)
    all_pass = all(passed for _, _, passed in results)
    for label, detail, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {label} — {detail}")

    if not all_pass:
        print("\nERROR: Verification failed after patching!")
        return 1

    # Save vanilla (unpatched) source — patches applied at build time
    UPSTREAM_PATH.write_text(vanilla)
    update_version_constant(new_version)
    print(f"\nUpdated upstream to {new_version}: {UPSTREAM_PATH}")
    print("Run `bun run build` to apply patches.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
