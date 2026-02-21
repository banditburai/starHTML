#!/usr/bin/env python3
"""
Hatchling build hook to build JavaScript from TypeScript during wheel creation.

This hook ensures that JavaScript plugins are built from TypeScript sources
before the wheel is packaged, allowing us to keep generated JS files out of git
while still including them in the distributed package.
"""

import subprocess
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class JavaScriptBuildError(Exception):
    """Raised when JavaScript build fails."""


def run_command(cmd: list[str], cwd: Path | None = None) -> None:
    """Run a command and raise JavaScriptBuildError if it fails."""
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        print(f"✅ Successfully ran: {' '.join(cmd)}")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {' '.join(cmd)}")
        print(f"   Exit code: {e.returncode}")
        print(f"   Stderr: {e.stderr}")
        print(f"   Stdout: {e.stdout}")
        raise JavaScriptBuildError(f"Failed to run {' '.join(cmd)}") from e


def _validate_and_collect(root_path: Path, build_data: dict[str, Any]) -> None:
    """Validate build outputs and register them as hatchling artifacts."""
    js_dir = root_path / "src" / "starhtml" / "static" / "js"

    if not (js_dir / "plugins").exists():
        raise JavaScriptBuildError(f"Plugins directory not created: {js_dir / 'plugins'}")
    if not (js_dir / "debugger").exists():
        raise JavaScriptBuildError(f"Debugger directory not created: {js_dir / 'debugger'}")

    # Datastar is the only file where an empty build is a silent, hard-to-debug failure
    datastar_path = js_dir / "datastar.js"
    if not datastar_path.exists():
        raise JavaScriptBuildError(f"Datastar file not created: {datastar_path}")
    if datastar_path.stat().st_size == 0:
        raise JavaScriptBuildError(f"Datastar file is empty: {datastar_path}")

    all_files = sorted(f for f in js_dir.rglob("*") if f.is_file())
    artifacts = build_data.setdefault("artifacts", [])
    for f in all_files:
        artifacts.append(str(f.relative_to(root_path)))

    print(f"✅ JavaScript build complete — {len(all_files)} files registered as artifacts:")
    for f in all_files:
        print(f"   - {f.relative_to(js_dir)}")


class CustomBuildHook(BuildHookInterface):
    """Build hook that builds JavaScript from TypeScript during packaging."""

    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """
        Initialize the build hook and build JavaScript from TypeScript.

        This method:
        1. Checks if bun is available (required for building)
        2. Installs JavaScript dependencies if needed
        3. Builds JavaScript plugins from TypeScript sources
        4. Ensures the built files are available for packaging
        """
        root_path = Path(self.root)

        print("🔨 Building JavaScript plugins from TypeScript...")

        if not (root_path / "typescript").exists():
            print("⚠️  No typescript directory found, skipping JavaScript build")
            return

        if not (root_path / "package.json").exists():
            print("⚠️  No package.json found, skipping JavaScript build")
            return

        try:
            run_command(["bun", "--version"], cwd=root_path)
        except (JavaScriptBuildError, FileNotFoundError):
            print("❌ bun is not available - JavaScript build will be skipped")
            print("   This is expected in some CI environments where JS is pre-built")
            return

        if not (root_path / "node_modules").exists():
            print("📦 Installing JavaScript dependencies...")
            run_command(["bun", "install", "--frozen-lockfile"], cwd=root_path)

        print("🏗️  Building JavaScript plugins...")
        run_command(["bun", "run", "build"], cwd=root_path)

        _validate_and_collect(root_path, build_data)
