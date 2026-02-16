"""StarHTML Debugger - auto-injected when debug=True."""

from .xtend import NotStr, Script


def setup_debugger(app):
    """Register the v2 StarElements debugger with the app.

    Falls back to a warning if starelements is not installed.
    """
    try:
        from .debugger_v2 import StarHTMLDebugger
    except ImportError:
        import sys

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
