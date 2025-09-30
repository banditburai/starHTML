"""Explicit Philosophy - Monster Hunter Arena

Demonstrates StarHTML's 'Explicit is Better' principle through clear cause-and-effect game mechanics.
"""

from typing import Any

from starhtml import *
from starhtml.datastar import f, js, switch, value

DAMAGE_RANGES = {"attack": (15, 25), "fireball": (35, 45), "monster_counter": (10, 20), "defend_reduced": (5, 10)}

COSTS = {"attack": 10, "fireball": 25, "heal": 20, "defend": 0}

REWARDS = {
    "attack_xp": 10,
    "attack_gold": 5,
    "fireball_xp": 20,
    "fireball_gold": 10,
    "heal_amount": 30,
    "defend_mana": 10,
    "levelup_xp": 100,
}

BUTTON_COLORS = {"attack": "black", "fireball": "orange-500", "heal": "green-500", "defend": "blue-500"}

MONSTER_NAMES = ["Goblin Warrior", "Orc Berserker", "Dark Wizard", "Stone Golem"]


def panel_container(*children, extra_classes: str = "") -> Div:
    return Div(*children, cls=f"p-4 bg-white border border-gray-200 {extra_classes}")


def stat_bar(label: str, current_signal: Any, max_signal: Any, color: str = "red", icon: Any = None) -> Div:
    return Div(
        Div(
            icon or "",
            Span(f"{label}: ", cls="text-xs text-gray-600"),
            Span(data_text=current_signal, cls=f"font-bold text-{color}-600"),
            Span(" / ", cls="text-gray-400 text-sm"),
            Span(data_text=max_signal, cls="text-gray-600 text-sm"),
            cls="mb-1 flex items-center gap-1",
        ),
        Div(
            Div(
                cls=f"h-5 bg-{color}-500 transition-all duration-300",
                data_style_width=f("{percent}%", percent=(current_signal / max_signal) * 100),
            ),
            cls="w-full bg-gray-200 rounded overflow-hidden",
        ),
    )


def battle_action_button(
    name: str, icon: str, description: str, color: str, actions: list, disabled_condition: Any
) -> Button:
    hover_color = color.replace("500", "600") if "500" in color else f"{color}-600"
    base_classes = f"px-4 py-3 bg-{color} hover:bg-{hover_color} text-white font-medium"
    state_classes = "disabled:bg-gray-400 disabled:cursor-not-allowed transition-all hover:scale-105 active:scale-95"
    layout_classes = "rounded-lg flex flex-col items-center w-full"

    return Button(
        Div(Icon(icon, width="20", height="20"), name, cls="flex items-center gap-2 justify-center mb-1"),
        Div(description, cls="text-xs opacity-75"),
        data_on_click=actions,
        data_attr_disabled=disabled_condition,
        cls=f"{base_classes} {state_classes} {layout_classes}",
    )


PIXEL_BACKGROUNDS = {
    "player": "linear-gradient(to bottom, #4A90E2 0%, #4A90E2 30%, #FFB6C1 30%, #FFB6C1 60%, #333 60%, #333 100%)",
    "goblin": "linear-gradient(to bottom, #6B8E23 0%, #6B8E23 40%, #8B4513 40%, #8B4513 70%, #556B2F 70%, #556B2F 100%)",
}


def pixel_character(char_type: str = "player") -> Div:
    return Div(
        cls=f"pixel-{char_type}",
        style=f"width: 48px; height: 48px; image-rendering: pixelated; border: 2px solid #000; box-shadow: 0 2px 4px rgba(0,0,0,0.2); background: {PIXEL_BACKGROUNDS.get(char_type, PIXEL_BACKGROUNDS['goblin'])};",
    )


def feature_badge(icon_name: str, text: str, color: str) -> Span:
    return Span(
        Icon(icon_name, width="16", height="16", cls=f"mr-1 text-{color}"),
        text,
        cls="inline-flex items-center text-sm text-gray-700 mr-6",
    )


def game_header() -> Div:
    return Div(
        H1("Explicit is Better", cls="text-2xl font-bold text-black mb-2"),
        P("Monster Hunter Arena - Every action has clear, traceable consequences", cls="text-gray-600 mb-4"),
        Div(
            feature_badge("material-symbols:visibility", "Every Action Visible", "blue-600"),
            feature_badge("material-symbols:analytics", "Clear Cause & Effect", "green-600"),
            feature_badge("material-symbols:code", "No Hidden Mechanics", "purple-600"),
            cls="mb-6 pb-4 border-b border-gray-200",
        ),
    )


def player_panel(
    player_hp: Any,
    player_max_hp: Any,
    player_mana: Any,
    player_max_mana: Any,
    player_xp: Any,
    player_max_xp: Any,
    player_level: Any,
    player_gold: Any,
) -> Div:
    return panel_container(
        Div(
            pixel_character("player"),
            Div(
                H4("Hero", cls="font-semibold text-sm"),
                Div("Level ", Span(data_text=player_level, cls="font-bold"), cls="text-xs text-gray-600"),
                cls="ml-3",
            ),
            cls="flex items-center mb-4",
        ),
        Div(
            stat_bar(
                "HP",
                player_hp,
                player_max_hp,
                "red",
                Icon("material-symbols:favorite", width="16", height="16", cls="text-red-500"),
            ),
            stat_bar(
                "MP",
                player_mana,
                player_max_mana,
                "blue",
                Icon("material-symbols:water-drop", width="16", height="16", cls="text-blue-500"),
            ),
            stat_bar(
                "XP",
                player_xp,
                player_max_xp,
                "green",
                Icon("material-symbols:star", width="16", height="16", cls="text-green-500"),
            ),
            cls="space-y-3",
        ),
        Div(
            Icon("material-symbols:toll", width="16", height="16", cls="text-yellow-600"),
            Span(data_text=player_gold, cls="font-bold text-yellow-600 text-lg ml-1"),
            Span(" Gold", cls="text-sm text-gray-600 ml-1"),
            cls="flex items-center mt-4 p-2 bg-yellow-50 rounded",
        ),
        extra_classes="md:col-span-1",
    )


def monster_panel(monster_hp: Any, monster_max_hp: Any, monster_name: Any) -> Div:
    return panel_container(
        Div(
            pixel_character("goblin"),
            Div(
                H4(data_text=monster_name, cls="font-semibold text-sm text-purple-600"),
                Span(
                    data_text=switch(
                        [
                            (monster_hp <= 0, "💀 Defeated"),
                            (monster_hp < 20, "🩸 Critical"),
                            (monster_hp < 40, "🤕 Wounded"),
                            (monster_hp < 60, "😤 Angry"),
                        ],
                        default="💪 Healthy",
                    ),
                    cls="text-xs",
                ),
                cls="ml-3",
            ),
            cls="flex items-center mb-3",
        ),
        stat_bar(
            "HP",
            monster_hp,
            monster_max_hp,
            "red",
            Icon("material-symbols:favorite", width="16", height="16", cls="text-red-600"),
        ),
        Div(
            P("Behavior:", cls="text-xs text-gray-600 mb-1"),
            P(
                f"Counters for {DAMAGE_RANGES['monster_counter'][0]}-{DAMAGE_RANGES['monster_counter'][1]} damage",
                cls="text-xs font-mono",
            ),
            P(
                f"Reduced to {DAMAGE_RANGES['defend_reduced'][0]}-{DAMAGE_RANGES['defend_reduced'][1]} when defending",
                cls="text-xs font-mono",
            ),
            cls="mt-3 p-2 bg-gray-50 rounded",
        ),
        extra_classes="md:col-span-1",
    )


def random_damage_js(min_dmg: int, max_dmg: int) -> str:
    return f"{min_dmg} + Math.floor(Math.random() * {max_dmg - min_dmg + 1})"


def attack_damage_js(min_dmg: int, max_dmg: int, attack_type: str) -> str:
    min_counter, max_counter = DAMAGE_RANGES["monster_counter"]
    return f"""
        const damage = {random_damage_js(min_dmg, max_dmg)};
        $monster_hp = Math.max(0, $monster_hp - damage);
        $combat_log.unshift(`{attack_type} for ${{damage}} damage!`);
        if ($monster_hp <= 0) {{
            $combat_log.unshift('🎉 Victory! Monster defeated!');
        }} else {{
            setTimeout(() => {{
                const counter = {random_damage_js(min_counter, max_counter)};
                $player_hp = Math.max(0, $player_hp - counter);
                $combat_log.unshift(`👹 Monster strikes back for ${{counter}} damage!`);
                if ($player_hp <= 0) {{
                    $combat_log.unshift('💀 You have been defeated! Click Reset to try again.');
                }}
            }}, 300);
        }}
    """


def defend_damage_js() -> str:
    min_dmg, max_dmg = DAMAGE_RANGES["defend_reduced"]
    return f"""
        if ($monster_hp > 0) {{
            setTimeout(() => {{
                const reducedDmg = {random_damage_js(min_dmg, max_dmg)};
                $player_hp = Math.max(0, $player_hp - reducedDmg);
                $combat_log.unshift(`👹 Monster attacks but you block! Only ${{reducedDmg}} damage taken`);
                if ($player_hp <= 0) {{
                    $combat_log.unshift('💀 You have been defeated! Click Reset to try again.');
                }}
            }}, 300);
        }}
    """


def battle_actions(
    player_mana: Any,
    player_hp: Any,
    player_max_hp: Any,
    player_max_mana: Any,
    player_xp: Any,
    player_gold: Any,
    monster_hp: Any,
    combat_log: Any,
) -> Div:
    return panel_container(
        H4("Battle Actions", cls="font-semibold mb-3"),
        Div(
            battle_action_button(
                "Attack",
                "material-symbols:swords",
                f"{COSTS['attack']} MP • {DAMAGE_RANGES['attack'][0]}-{DAMAGE_RANGES['attack'][1]} DMG",
                BUTTON_COLORS["attack"],
                [
                    player_mana.sub(COSTS["attack"]),
                    player_xp.add(REWARDS["attack_xp"]),
                    player_gold.add(REWARDS["attack_gold"]),
                    js(attack_damage_js(*DAMAGE_RANGES["attack"], "⚔️ Attack")),
                ],
                (player_mana < COSTS["attack"]) | (monster_hp <= 0) | (player_hp <= 0),
            ),
            battle_action_button(
                "Fireball",
                "material-symbols:local-fire-department",
                f"{COSTS['fireball']} MP • {DAMAGE_RANGES['fireball'][0]}-{DAMAGE_RANGES['fireball'][1]} DMG",
                BUTTON_COLORS["fireball"],
                [
                    player_mana.sub(COSTS["fireball"]),
                    player_xp.add(REWARDS["fireball_xp"]),
                    player_gold.add(REWARDS["fireball_gold"]),
                    js(attack_damage_js(*DAMAGE_RANGES["fireball"], "🔥 Fireball")),
                ],
                (player_mana < COSTS["fireball"]) | (monster_hp <= 0) | (player_hp <= 0),
            ),
            battle_action_button(
                "Heal",
                "material-symbols:healing",
                f"{COSTS['heal']} MP",
                BUTTON_COLORS["heal"],
                [
                    player_mana.sub(COSTS["heal"]),
                    player_hp.set((player_hp + REWARDS["heal_amount"]).min(player_max_hp)),
                    combat_log.prepend(
                        f(
                            "💚 Healed for {amount} HP",
                            amount=value(REWARDS["heal_amount"]).min(player_max_hp - player_hp),
                        )
                    ),
                ],
                (player_mana < COSTS["heal"]) | (player_hp >= player_max_hp) | (player_hp <= 0),
            ),
            battle_action_button(
                "Defend",
                "material-symbols:shield",
                "Free • Gain MP • Reduce damage",
                BUTTON_COLORS["defend"],
                [
                    player_mana.set((player_mana + REWARDS["defend_mana"]).min(player_max_mana)),
                    combat_log.prepend(
                        f(
                            "🛡️ Defending, gained {amount} MP",
                            amount=value(REWARDS["defend_mana"]).min(player_max_mana - player_mana),
                        )
                    ),
                    js(defend_damage_js()),
                ],
                (player_hp <= 0) | (monster_hp <= 0),
            ),
            cls="grid grid-cols-2 gap-2 mb-3",
        ),
        extra_classes="md:col-span-1",
    )


def utility_buttons(
    monster_hp: Any,
    monster_max_hp: Any,
    monster_name: Any,
    player_level: Any,
    player_max_hp: Any,
    player_max_mana: Any,
    player_hp: Any,
    player_mana: Any,
    player_xp: Any,
    player_gold: Any,
    combat_log: Any,
) -> Div:
    is_monster_alive = monster_hp > 0
    can_level_up = player_xp >= 100

    return Div(
        Button(
            "New Monster",
            data_on_click=[
                monster_hp.set(80),
                monster_max_hp.set(80),
                monster_name.set(
                    js(f"{MONSTER_NAMES}[Math.floor(Math.random() * {len(MONSTER_NAMES)})]".replace("'", '"'))
                ),
                combat_log.prepend("⚔️ New challenger appears!"),
            ],
            data_attr_disabled=is_monster_alive,
            cls="px-3 py-2 text-sm border border-gray-300 hover:border-gray-500 disabled:bg-gray-100 transition-colors mr-2",
        ),
        Button(
            "Level Up",
            data_on_click=[
                player_level.add(1),
                player_max_hp.add(20),
                player_max_mana.add(10),
                player_hp.set(player_max_hp),
                player_mana.set(player_max_mana),
                player_xp.sub(REWARDS["levelup_xp"]),
                combat_log.prepend("⬆️ LEVEL UP!"),
            ],
            data_attr_disabled=~can_level_up,
            cls="px-3 py-2 text-sm bg-yellow-500 text-white hover:bg-yellow-600 disabled:bg-gray-400 transition-colors mr-2",
        ),
        Button(
            "Reset",
            data_on_click=[
                player_hp.set(100),
                player_mana.set(50),
                player_xp.set(0),
                player_level.set(1),
                player_gold.set(0),
                monster_hp.set(80),
                combat_log.set([]),
            ],
            cls="px-3 py-2 text-sm border border-gray-300 text-gray-600 hover:border-gray-500 transition-colors",
        ),
        cls="flex",
    )


def game_state_overlay(emoji: str, title: str, message: str, hint: str, color: str, condition: Any) -> Div:
    return Div(
        Div(
            Div(f"{emoji} {title}", cls=f"text-2xl font-bold text-{color}-600 mb-2"),
            P(message, cls="text-sm text-gray-600 mb-3"),
            P(hint, cls="text-xs text-gray-500"),
            cls=f"text-center p-6 bg-{color}-50 border-2 border-{color}-300 rounded-lg",
        ),
        data_show=condition,
        cls="absolute inset-0 flex items-center justify-center bg-white/90 backdrop-blur-sm",
    )


def combat_log_panel(combat_log: Any, player_hp: Any, monster_hp: Any) -> Div:
    return panel_container(
        H4("Combat Log", cls="font-semibold mb-3"),
        Div(
            Div(
                "No actions yet...",
                Br(),
                "Start attacking!",
                cls="text-center py-8 text-gray-400 text-sm",
                data_show=combat_log.length == 0,
            ),
            Div(
                *[
                    Div(
                        data_text=combat_log[i],
                        data_show=i < combat_log.length,
                        cls=f"py-1 text-sm border-b border-gray-100 {'font-semibold' if i == 0 else f'opacity-{100 - i * 8}'}",
                    )
                    for i in range(10)
                ],
                data_show=combat_log.length > 0,
            ),
            game_state_overlay(
                "💀",
                "DEFEATED",
                "Your hero has fallen in battle.",
                "Click the Reset button to try again.",
                "red",
                player_hp <= 0,
            ),
            game_state_overlay(
                "🎉",
                "VICTORY!",
                "You have defeated the monster!",
                "Click New Monster to face another challenger.",
                "green",
                (monster_hp <= 0) & (player_hp > 0),
            ),
            cls="h-64 overflow-y-auto relative",
        ),
        extra_classes="md:col-span-1",
    )


def code_example() -> Div:
    return panel_container(
        H4("How It Works - Explicit Actions", cls="font-semibold mb-3"),
        P("Every button action is explicit and traceable:", cls="text-sm text-gray-600 mb-3"),
        Pre(
            Code(
                f"""Button(
    "⚔️ Attack",
    Span("{COSTS["attack"]} MP • {DAMAGE_RANGES["attack"][0]}-{DAMAGE_RANGES["attack"][1]} DMG"),
    data_on_click=[
        player_mana.sub({COSTS["attack"]}),
        player_xp.add({REWARDS["attack_xp"]}),
        player_gold.add({REWARDS["attack_gold"]}),
        damage_and_log_action()
    ],
    data_attr_disabled=(player_mana < {COSTS["attack"]}) | (monster_hp <= 0)
)""",
                cls="text-xs",
            ),
            cls="p-4 bg-gray-900 text-green-400 rounded overflow-x-auto",
        ),
        extra_classes="col-span-full",
    )


def explicit_section() -> Div:
    return Div(
        (player_hp := Signal("player_hp", 100)),
        (player_max_hp := Signal("player_max_hp", 100)),
        (player_mana := Signal("player_mana", 50)),
        (player_max_mana := Signal("player_max_mana", 50)),
        (player_xp := Signal("player_xp", 0)),
        (player_max_xp := Signal("player_max_xp", 100)),
        (player_level := Signal("player_level", 1)),
        (player_gold := Signal("player_gold", 0)),
        (monster_hp := Signal("monster_hp", 80)),
        (monster_max_hp := Signal("monster_max_hp", 80)),
        (monster_name := Signal("monster_name", "Goblin Warrior")),
        (combat_log := Signal("combat_log", [])),
        Style("""
            .pixel-hero, .pixel-goblin {
                animation: idle-bounce 1s ease-in-out infinite;
            }
            @keyframes idle-bounce {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-2px); }
            }
        """),
        game_header(),
        Div(
            Div(
                player_panel(
                    player_hp,
                    player_max_hp,
                    player_mana,
                    player_max_mana,
                    player_xp,
                    player_max_xp,
                    player_level,
                    player_gold,
                ),
                monster_panel(monster_hp, monster_max_hp, monster_name),
                cls="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4",
            ),
            Div(
                Div(
                    battle_actions(
                        player_mana,
                        player_hp,
                        player_max_hp,
                        player_max_mana,
                        player_xp,
                        player_gold,
                        monster_hp,
                        combat_log,
                    ),
                    utility_buttons(
                        monster_hp,
                        monster_max_hp,
                        monster_name,
                        player_level,
                        player_max_hp,
                        player_max_mana,
                        player_hp,
                        player_mana,
                        player_xp,
                        player_gold,
                        combat_log,
                    ),
                    cls="space-y-3",
                ),
                combat_log_panel(combat_log, player_hp, monster_hp),
                cls="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4",
            ),
            code_example(),
            cls="p-2 sm:p-4 bg-gray-50",
        ),
    )


app, rt = star_app(
    title="Explicit Philosophy - Monster Hunter Arena",
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
            "⚠️ Development Mode - Explicit Philosophy Section",
            cls="bg-yellow-100 p-4 mb-4 text-center font-mono text-sm",
        ),
        explicit_section(),
    )


if __name__ == "__main__":
    print("🚀 Explicit Philosophy - Development Mode")
    print("Visit: http://localhost:5092/")

    serve(port=5092)
