"""StarHTML Debugger - auto-injected when debug=True."""

from .xtend import Script, NotStr


def debugger_hdrs():
    """Return headers that inject the debugger script."""
    return (
        Script(src="/_pkg/starhtml/plugins/debugger.js", type="module"),
    )


def debugger_ftrs():
    """Return footer elements: the debugger component + init script."""
    return (
        NotStr('<starhtml-debugger></starhtml-debugger>'),
        Script("import {init} from '/_pkg/starhtml/plugins/debugger.js'; init();", type="module"),
    )
