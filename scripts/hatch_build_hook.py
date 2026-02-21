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

    # Plugins
    plugins_dir = js_dir / "plugins"
    if not plugins_dir.exists():
        raise JavaScriptBuildError(f"Plugins directory not created: {plugins_dir}")

    built_files = list(plugins_dir.glob("*.js"))
    if not built_files:
        raise JavaScriptBuildError("No JavaScript files found after build")

    core_files = {"persist.js", "scroll.js", "resize.js", "drag.js", "canvas.js", "position.js", "split.js"}
    missing_core = core_files - {f.name for f in built_files}
    if missing_core:
        raise JavaScriptBuildError(f"Missing core JavaScript files after build: {missing_core}")

    print(f"✅ JavaScript build complete! Generated {len(built_files)} plugin files:")
    for file in sorted(built_files):
        print(f"   - {file.name}")

    # Debugger
    debugger_dir = js_dir / "debugger"
    if not debugger_dir.exists():
        raise JavaScriptBuildError(f"Debugger directory not created: {debugger_dir}")

    debugger_core_files = {"capture.js", "setup.js", "signals.js", "timeline.js", "dom-observer.js", "debugger.css"}
    debugger_files = list(debugger_dir.glob("*"))
    missing_debugger = debugger_core_files - {f.name for f in debugger_files}
    if missing_debugger:
        raise JavaScriptBuildError(f"Missing debugger files after build: {missing_debugger}")

    print(f"✅ Debugger build verified! Found {len(debugger_files)} files:")
    for file in sorted(debugger_files):
        print(f"   - {file.name}")

    # Datastar
    datastar_path = js_dir / "datastar.js"
    if not datastar_path.exists():
        raise JavaScriptBuildError(f"Datastar file not created: {datastar_path}")
    ds_size = datastar_path.stat().st_size
    if ds_size == 0:
        raise JavaScriptBuildError(f"Datastar file is empty: {datastar_path}")
    print(f"✅ Datastar build verified: {datastar_path.name} ({ds_size} bytes)")

    # Register artifacts
    artifacts = build_data.setdefault("artifacts", [])
    for file_path in built_files:
        rel_path = f"src/starhtml/static/js/plugins/{file_path.name}"
        if rel_path not in artifacts:
            artifacts.append(rel_path)

    for file_path in debugger_files:
        rel_path = f"src/starhtml/static/js/debugger/{file_path.name}"
        if rel_path not in artifacts:
            artifacts.append(rel_path)

    datastar_rel = "src/starhtml/static/js/datastar.js"
    if datastar_rel not in artifacts:
        artifacts.append(datastar_rel)

    print(f"📦 Added {len(built_files)} plugin + {len(debugger_files)} debugger + 1 datastar files to build artifacts")


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
