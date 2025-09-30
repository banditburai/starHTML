"""Composable Philosophy - Crafting Empire Game

Interactive demo showing how StarHTML components compose naturally.
"""

from typing import Any

from starhtml import *
from starhtml.datastar import all, js


def float_animation_js(rgb: str) -> str:
    return f"""
        const btn = event.currentTarget;
        const rect = btn.getBoundingClientRect();
        const floater = document.createElement('div');
        floater.textContent = '+1';
        floater.style.position = 'fixed';
        floater.style.left = (rect.left + rect.width/2) + 'px';
        floater.style.top = (rect.top - 10) + 'px';
        floater.style.color = '{rgb}';
        floater.style.fontWeight = 'bold';
        floater.style.pointerEvents = 'none';
        floater.style.zIndex = '1000';
        floater.style.animation = 'float-up 0.8s ease-out forwards';
        floater.style.transform = 'translateX(-50%)';
        document.body.appendChild(floater);
        setTimeout(() => floater.remove(), 800);
    """


def panel_container(*children, extra_classes: str = "") -> Div:
    return Div(*children, cls=f"p-4 bg-white border border-gray-200 rounded-lg {extra_classes}")


def collapsible_code_section(code: str, signal: Any, cls: str = "text-xs") -> Div:
    return Div(
        Pre(Code(code, cls=cls), cls="bg-gray-50 p-3 rounded text-xs overflow-x-auto"), data_show=signal, cls="mt-3"
    )


def section_header_with_toggle(title: str, toggle_signal: Any) -> Div:
    return Div(
        H4(title, cls="font-semibold mb-2 inline-block"),
        Button(
            data_text=toggle_signal.if_("Hide Code", "Show Code"),
            data_on_click=toggle_signal.toggle(),
            cls="ml-2 text-xs text-gray-500 hover:text-gray-700 px-2 py-1 hover:bg-gray-100 rounded",
        ),
        cls="mb-3",
    )


def colored_annotation(text: str, color: str) -> Div:
    return Div(text, cls=f"text-xs text-{color}-600 italic mt-3 mb-3")


RESOURCES = {
    "wood": {"icon": "tabler:tree", "color": "green", "rgb": "rgb(34 197 94)"},
    "stone": {"icon": "tabler:diamond", "color": "gray", "rgb": "rgb(107 114 128)"},
    "gold": {"icon": "tabler:coin", "color": "yellow", "rgb": "rgb(234 179 8)"},
    "silicon": {"icon": "tabler:cpu", "color": "blue", "rgb": "rgb(59 130 246)"},
}


def resource_icon(resource: str) -> str:
    return RESOURCES.get(resource, {}).get("icon", "tabler:help")


def resource_color(resource: str) -> str:
    return RESOURCES.get(resource, {}).get("color", "gray")


def resource_rgb(resource: str) -> str:
    return RESOURCES.get(resource, {}).get("rgb", "rgb(107 114 128)")


def resources_panel(wood: Any, stone: Any, gold: Any, silicon: Any, show_code: Any) -> Div:
    resources = [("Wood", wood), ("Stone", stone), ("Gold", gold), ("Silicon", silicon)]

    return panel_container(
        section_header_with_toggle("Resources", show_code),
        Div(*[resource_display(name, signal) for name, signal in resources], cls="grid grid-cols-2 gap-4"),
        colored_annotation("↑ Signal definitions + data_text binding + reactive updates", "green"),
        collapsible_code_section(
            """(wood := Signal("wood", 2))

def resource_display(label, signal):
    return Div(Icon(), Div(data_text=signal))""",
            show_code,
        ),
        extra_classes="md:col-span-1",
    )


def gathering_panel(wood: Any, stone: Any, gold: Any, show_code: Any) -> Div:
    return panel_container(
        section_header_with_toggle("Gather Resources", show_code),
        Div(
            gather_button("Wood", wood),
            gather_button("Stone", stone),
            gather_button("Gold", gold),
            cls="grid grid-cols-1 sm:grid-cols-3 gap-2",
        ),
        colored_annotation("↑ data_on_click=[signal.add(1), js('animate')] + floating feedback", "blue"),
        P("Each gather adds 1 to your resource count", cls="text-xs text-gray-500 mt-3"),
        collapsible_code_section(
            """def gather_button(resource, signal):
    return Button(
        Icon(resource_icon(resource), width="20", height="20"),
        Span(f"Gather {resource}"),
        data_on_click=[signal.add(1), js('animate')]
    )""",
            show_code,
        ),
        extra_classes="md:col-span-2",
    )


def tools_panel(signals: dict[str, Any], show_code: Any) -> Div:
    return panel_container(
        section_header_with_toggle("Basic Tools", show_code),
        Div(
            craft_button("Hammer", "tabler:hammer", {"wood": 2, "stone": 1}, "Crafted a hammer!", "orange", signals),
            craft_button("Pickaxe", "mdi:pickaxe", {"wood": 1, "stone": 2}, "Forged a pickaxe!", "purple", signals),
            craft_button("Shovel", "tabler:shovel", {"wood": 3}, "Built a shovel!", "amber", signals),
            cls="space-y-2",
        ),
        colored_annotation("↑ craft_button() + all() conditions + Signal.sub() actions", "orange"),
        collapsible_code_section(
            """def craft_button(item, requirements, signals):
    conditions = [signals[res] >= amt for res, amt in requirements.items()]
    actions = [signals[res].sub(amt) for res, amt in requirements.items()]
    return Button(item, data_on_click=actions, data_attr_disabled=~all(*conditions))""",
            show_code,
        ),
        extra_classes="md:col-span-1",
    )


def technology_panel(signals: dict[str, Any], show_code: Any) -> Div:
    return panel_container(
        section_header_with_toggle("Technology", show_code),
        Div(
            craft_button(
                "Silicon Wafer",
                "tabler:cpu",
                {"stone": 3, "gold": 1},
                "Refined silicon from sand!",
                "blue",
                signals,
                target_signal="silicon",
                achievement="Silicon Valley",
            ),
            craft_button(
                "Transistor", "tabler:cpu", {"silicon": 2, "gold": 1}, "Built a transistor!", "indigo", signals
            ),
            craft_button(
                "Circuit Board",
                "tabler:cpu-2",
                {"silicon": 3, "gold": 2},
                "Assembled a circuit board!",
                "purple",
                signals,
                achievement="Hardware Architect",
            ),
            cls="space-y-2",
        ),
        colored_annotation("↑ target_signal='silicon' + achievements.push() + conditional crafting", "purple"),
        extra_classes="md:col-span-1",
    )


def ultimate_goal_panel(signals: dict[str, Any], gpus: Any) -> Div:
    return panel_container(
        H4("Ultimate Prize", cls="font-semibold mb-3"),
        craft_button(
            "GPU",
            "tabler:device-desktop-analytics",
            {"silicon": 5, "gold": 3, "circuit": 1},
            "GPU CREATED! Digital pickaxes for the AI gold rush!",
            "green",
            signals,
            target_signal="gpus",
            achievement="Digital Pickaxe Seller",
        ),
        colored_annotation("↑ tools.contains() condition + target_signal pattern", "emerald"),
        Div(
            Icon("tabler:device-desktop-analytics", width="32", height="32", cls="text-green-600"),
            Div(
                P("GPUs Owned", cls="text-xs text-gray-600"),
                Div(data_text=gpus, cls="text-3xl font-bold text-green-700"),
            ),
            cls="flex items-center gap-4 mt-4 p-3 bg-green-50 rounded-lg",
        ),
        extra_classes="md:col-span-1",
    )


def inventory_panel(tools: Any, achievements: Any, show_code: Any) -> Div:
    return panel_container(
        section_header_with_toggle("Inventory", show_code),
        Div(data_text=tools.if_(tools.join(" • "), "Empty"), cls="min-h-[60px] p-3 bg-gray-50 rounded"),
        colored_annotation("↑ tools.if_(join, 'Empty') conditional display", "indigo"),
        Div(
            P("Achievements", cls="text-xs font-semibold text-purple-600 mb-2"),
            Div(
                data_text=achievements.if_(achievements.join(" • "), "None yet"),
                cls="text-xs text-gray-600 p-2 bg-purple-50 rounded",
            ),
            cls="mt-3",
        ),
        collapsible_code_section("""data_text=tools.if_(tools.join(" • "), "Empty")""", show_code),
        extra_classes="md:col-span-1",
    )


def action_log_panel(action_log: Any) -> Div:
    return panel_container(
        H4("Action Log", cls="font-semibold mb-3"),
        Div(
            Div(
                *[Div(data_text=f"$action_log[{i}]", cls="text-sm text-gray-700 mb-1") for i in range(5)],
                cls="space-y-1",
            ),
            cls="min-h-[120px] max-h-[120px] overflow-y-auto p-3 bg-gray-50 rounded",
        ),
        P("Recent actions appear here", cls="text-xs text-gray-500 mt-2"),
        extra_classes="md:col-span-2",
    )


def resource_display(label: str, signal: Any) -> Div:
    key = label.lower()
    return Div(
        Icon(resource_icon(key), width="20", height="20", cls=f"text-{resource_color(key)}-600"),
        Div(
            Span(label, cls="text-xs text-gray-600"),
            Div(data_text=signal, cls=f"text-2xl font-bold text-{resource_color(key)}-700"),
        ),
        cls="flex items-center gap-3",
    )


def gather_button(resource: str, signal: Any) -> Button:
    key = resource.lower()
    color = resource_color(key)
    icon_name = resource_icon(key)
    rgb = resource_rgb(key)

    return Button(
        Icon(icon_name, width="20", height="20", cls=f"text-{color}-600"),
        Span(f"Gather {resource}", cls="ml-2"),
        data_on_click=[signal.add(1), js(float_animation_js(rgb))],
        cls=f"px-3 py-2 bg-{color}-50 hover:bg-{color}-100 text-{color}-800 border border-{color}-200 rounded-lg transition-all hover:scale-105 active:scale-95 w-full",
    )


def craft_button(
    item: str,
    icon_name: str,
    requirements: dict[str, int],
    message: str,
    color: str,
    signals: dict[str, Any],
    target_signal: str | None = None,
    achievement: str | None = None,
) -> Button:
    req_text = " • ".join(f"{amount} {resource}" for resource, amount in requirements.items() if amount > 0)

    resource_signals = {
        "wood": signals["wood"],
        "stone": signals["stone"],
        "gold": signals["gold"],
        "silicon": signals["silicon"],
    }

    conditions = [
        resource_signals[res] >= amt for res, amt in requirements.items() if amt > 0 and res in resource_signals
    ]
    if requirements.get("circuit", 0) > 0:
        conditions.append(signals["tools"].contains("Circuit Board"))

    actions = [
        resource_signals[res].sub(amt) for res, amt in requirements.items() if amt > 0 and res in resource_signals
    ]

    actions.extend(
        [signals["action_log"].unshift(message), signals["action_log"].set(signals["action_log"].slice(0, 10))]
    )

    if target_signal == "silicon":
        actions.append(resource_signals["silicon"].add(1))
    elif target_signal == "gpus":
        actions.append(Signal("gpus", _ref_only=True).add(1))
    else:
        actions.append(signals["tools"].append(item))

    if achievement:
        actions.append(
            (~signals["achievements"].contains(achievement)).then(signals["achievements"].append(achievement))
        )

    return Button(
        Div(
            Icon(icon_name, width="18", height="18", cls=f"text-{color}-600"),
            Div(
                Span(item, cls="font-semibold text-sm"),
                Div(req_text, cls="text-xs text-gray-500") if req_text else "",
            ),
            cls="flex items-center gap-2",
        ),
        data_on_click=actions,
        data_attr_disabled=~all(*conditions) if conditions else js("false"),
        cls=f"px-3 py-2 bg-white hover:bg-{color}-50 border border-gray-200 hover:border-{color}-300 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed transition-all text-left w-full",
    )


def composable_section():
    return Div(
        (wood := Signal("wood", 2)),
        (stone := Signal("stone", 1)),
        (gold := Signal("gold", 0)),
        (silicon := Signal("silicon", 0)),
        (tools := Signal("tools", [])),
        (gpus := Signal("gpus", 0)),
        (achievements := Signal("achievements", [])),
        (
            action_log := Signal(
                "action_log", ["Welcome to the Crafting Empire!", "Gather resources and build your way to GPUs!"]
            )
        ),
        (show_resources_code := Signal("show_resources_code", False)),
        (show_gather_code := Signal("show_gather_code", False)),
        (show_tools_code := Signal("show_tools_code", False)),
        (show_tech_code := Signal("show_tech_code", False)),
        (show_inventory_code := Signal("show_inventory_code", False)),
        Style("""
            @keyframes float-up {
                0% { opacity: 1; transform: translateY(0); }
                100% { opacity: 0; transform: translateY(-30px); }
            }
        """),
        Div(
            H1("Composable Primitives", cls="text-2xl font-bold text-black mb-2"),
            P("Build complex systems from simple, reusable components", cls="text-gray-600 mb-4"),
            Div(
                Span(
                    Icon("tabler:puzzle", width="16", height="16", cls="mr-1 text-blue-600"),
                    "Reusable Components",
                    cls="inline-flex items-center text-sm text-gray-700 mr-6",
                ),
                Span(
                    Icon("tabler:share", width="16", height="16", cls="mr-1 text-green-600"),
                    "Shared State",
                    cls="inline-flex items-center text-sm text-gray-700 mr-6",
                ),
                Span(
                    Icon("tabler:layers-linked", width="16", height="16", cls="mr-1 text-purple-600"),
                    "Complex from Simple",
                    cls="inline-flex items-center text-sm text-gray-700",
                ),
                cls="mb-6 pb-4 border-b border-gray-200",
            ),
        ),
        (
            craft_signals := {
                "wood": wood,
                "stone": stone,
                "gold": gold,
                "silicon": silicon,
                "tools": tools,
                "action_log": action_log,
                "achievements": achievements,
            }
        ),
        Div(
            Div(
                resources_panel(wood, stone, gold, silicon, show_resources_code),
                gathering_panel(wood, stone, gold, show_gather_code),
                cls="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4",
            ),
            Div(
                tools_panel(craft_signals, show_tools_code),
                technology_panel(craft_signals, show_tech_code),
                ultimate_goal_panel(craft_signals, gpus),
                cls="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4",
            ),
            Div(
                inventory_panel(tools, achievements, show_inventory_code),
                action_log_panel(action_log),
                cls="grid grid-cols-1 md:grid-cols-3 gap-4",
            ),
            cls="p-2 sm:p-4 bg-gray-50",
        ),
    )


app, rt = star_app(
    title="Composable Philosophy - StarHTML",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body {
                background: white;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                -webkit-font-smoothing: antialiased;
            }
        """),
    ],
    iconify=True,
)


@rt("/")
def dev_home():
    return Div(
        Div(
            "⚠️ Development Mode - Composable Philosophy Section",
            cls="bg-yellow-100 p-4 mb-4 text-center font-mono text-sm",
        ),
        composable_section(),
    )


if __name__ == "__main__":
    print("🚀 Composable Philosophy - Development Mode")
    print("Visit: http://localhost:5093/")
    serve(port=5093)
