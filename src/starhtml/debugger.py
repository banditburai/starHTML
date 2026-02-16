"""StarHTML Debugger - auto-injected when debug=True."""

from .xtend import Script, NotStr


def debugger_hdrs():
    return (
        Script(src="/_pkg/starhtml/plugins/debugger.js", type="module"),
    )


def debugger_ftrs():
    return (
        NotStr('<starhtml-debugger></starhtml-debugger>'),
        Script("import {init} from '/_pkg/starhtml/plugins/debugger.js'; init();", type="module"),
    )
