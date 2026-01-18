#!/usr/bin/env python3
"""Update bundled datastar.js to a specific version."""

import re
import sys
from pathlib import Path
from urllib.request import urlopen

STARAPP_PATH = Path(__file__).parent.parent / "src" / "starhtml" / "starapp.py"
STATIC_PATH = Path(__file__).parent.parent / "src" / "starhtml" / "static" / "datastar.js"
CDN_URL = "https://cdn.jsdelivr.net/gh/starfederation/datastar@{version}/bundles/datastar.js"


def get_current_version() -> str:
    content = STARAPP_PATH.read_text()
    match = re.search(r'DATASTAR_VERSION\s*=\s*["\']([^"\']+)["\']', content)
    return match.group(1) if match else "unknown"


def update_version_constant(new_version: str) -> None:
    content = STARAPP_PATH.read_text()
    updated = re.sub(
        r'(DATASTAR_VERSION\s*=\s*["\'])[^"\']+(["\'])',
        rf"\g<1>{new_version}\g<2>",
        content,
    )
    STARAPP_PATH.write_text(updated)


def download_datastar(version: str) -> str:
    url = CDN_URL.format(version=version)
    print(f"Downloading from {url}")
    with urlopen(url) as response:
        return response.read().decode("utf-8")


def main():
    current = get_current_version()
    print(f"Current version: {current}")

    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <version>")
        print(f"Example: {sys.argv[0]} 1.0.0-RC.7")
        sys.exit(1)

    new_version = sys.argv[1]
    print(f"Updating to: {new_version}")

    js_content = download_datastar(new_version)
    STATIC_PATH.write_text(js_content)
    print(f"Written {len(js_content)} bytes to {STATIC_PATH}")

    update_version_constant(new_version)
    print(f"Updated DATASTAR_VERSION in {STARAPP_PATH}")

    print("Done!")


if __name__ == "__main__":
    main()
