"""Shared components for StarHTML web demos and documentation."""

from pathlib import Path

from starlette.responses import HTMLResponse

from starhtml import *

try:
    from starlighter import highlight
except ImportError:
    highlight = None


async def get_source_code(req):
    filename = req.path_params["filename"]

    for base_path in [Path(__file__).parent / "demos", Path(__file__).parent]:
        demo_file = base_path / filename
        if demo_file.exists():
            code = demo_file.read_text()
            break
    else:
        return HTMLResponse(f"<pre class='text-red-400'>File not found: {filename}</pre>", status_code=404)

    highlighted_code = highlight(code, language="python") if highlight else f"<pre><code>{code}</code></pre>"

    return HTMLResponse(to_xml(Div(NotStr(str(highlighted_code)), cls="h-full overflow-auto")))


def _menu_link(icon, text, href, signal, icon_cls="", external=False):
    """Helper for creating dropdown menu links."""
    return A(
        Icon(icon, width="16", height="16", cls=icon_cls),
        Span(text, cls="ml-3"),
        href=href,
        **({"target": "_blank", "rel": "noopener noreferrer"} if external else {}),
        cls="flex items-center px-4 py-3 hover:bg-gray-50 transition-colors",
        data_on_click=signal.set(False),
    )


def support_dropdown(signal=None):
    if signal is None:
        signal = Signal("support_dropdown", False)

    # Extract signal name from string representation
    signal_str = str(signal)
    if signal_str.startswith("$"):
        signal_name = signal_str[1:]  # Remove the $ prefix
    else:
        signal_name = "support_dropdown"

    button_id = f"{signal_name}_button"
    menu_id = f"{signal_name}_menu"

    menu_items = [
        _menu_link(
            "tabler:brand-github", "Star on GitHub", "https://github.com/banditburai/starHTML", signal, external=True
        ),
        _menu_link(
            "tabler:coffee", "Buy us a coffee", "https://ko-fi.com/promptsiren", signal, "text-amber-500", external=True
        ),
        _menu_link("tabler:code-dots", "Interactive Demos", "/demos/", signal),
    ]

    return Div(
        Button(
            Icon(
                "tabler:star", width="18", height="18", cls="text-gray-400 group-hover:text-amber-500 transition-colors"
            ),
            Icon("tabler:chevron-down", width="14", height="14", cls="ml-1 text-gray-400"),
            data_on_click=signal.toggle(),
            cls="flex items-center px-2 sm:px-3 py-1.5 rounded-md hover:bg-gray-50 transition-all group",
            id=button_id,
        ),
        Div(
            *menu_items,
            data_position=(button_id, dict(placement="bottom-end", flip=True, shift=True, offset=8, container="none")),
            data_show=signal,
            id=menu_id,
            style="display: none",
            cls="w-56 bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden z-[1000]",
        ),
        cls="",
    )
