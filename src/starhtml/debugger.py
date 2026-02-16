"""StarHTML Debugger - auto-injected when debug=True."""

import sys

from .xtend import NotStr, Script


def setup_debugger(app):
    """Register the v2 StarElements debugger with the app.

    Falls back to a warning if starelements is not installed.
    The component setup script also calls capture.init() as a no-op
    safeguard — the early hdrs script ensures capture starts first.
    """
    try:
        from .debugger_v2 import StarHTMLDebugger
    except ImportError as exc:
        if "starelements" not in str(exc):
            raise
        print(
            "WARNING: starelements not installed — debugger disabled. "
            "Install with: uv pip install 'starhtml[debug]'",
            file=sys.stderr,
        )
        return

    app.register(StarHTMLDebugger)

    # Early capture init — start intercepting SSE events before component mounts
    app.hdrs.append(
        Script(
            "import {init} from '/_pkg/starhtml/plugins/debugger-capture.js'; init();",
            type="module",
        )
    )

    # Component tag in footer — instantiates the debugger panel
    app.ftrs.append(NotStr("<starhtml-debugger></starhtml-debugger>"))
