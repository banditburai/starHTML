"""Datastar integration for StarHTML - attribute processing and element creation."""

import json
import re
from typing import Any

from fastcore.xml import NotStr

from .utils import _camel_to_kebab

__all__ = []

# =============================================================================
# Helper Functions - Extracted patterns for code reuse
# =============================================================================


def _convert_boolean_to_html_string(value: Any) -> str:
    """Convert boolean values to HTML attribute strings."""
    return "true" if value is True else "false" if value is False else str(value)


def _wrap_nonempty_string(value: Any) -> Any:
    """Wrap non-empty strings in NotStr, pass through other values."""
    return NotStr(value) if isinstance(value, str) and value else value


def _process_datastar_attrs(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Process ds_* attributes and transform them to data-* attributes."""
    processed = {}
    for key, value in kwargs.items():
        if not key.startswith("ds_"):
            processed[key] = value
            continue

        # Sort by length (longest first) to match most specific patterns first
        handler = _handle_default
        for prefix in sorted(_ATTR_HANDLERS.keys(), key=len, reverse=True):
            if key.startswith(prefix):
                handler = _ATTR_HANDLERS[prefix]
                break

        data_key, data_value = handler(key, value)
        processed[data_key] = data_value

    return processed


def _handle_signals(key: str, value: Any) -> tuple[str, str]:
    """Handler for ds_signals."""
    if isinstance(value, dict):
        return "data-signals", json.dumps(value)
    # For backward compatibility, pass through non-dict values as-is
    return "data-signals", value


def _handle_persist(key: str, value: Any) -> tuple[str, str]:
    """Handler for ds_persist and ds_persist__session."""
    data_key = "data-persist__session" if "session" in key else "data-persist"
    return data_key, _process_persist_value(value)


def _handle_on(key: str, value: Any) -> tuple[str, Any]:
    """Handler for ds_on_* events."""
    event_part = key[len("ds_on_") :]
    data_key = _handle_event_key(event_part)
    # Only wrap non-empty strings in NotStr
    return data_key, _wrap_nonempty_string(value)


def _handle_attr(key: str, value: Any) -> tuple[str, Any]:
    """Handler for ds_attr_*."""
    attr_name = key[len("ds_attr_") :].replace("_", "-")
    return f"data-attr-{attr_name}", value


def _handle_style(key: str, value: Any) -> tuple[str, Any]:
    """Handler for ds_style_*."""
    style_name = key[len("ds_style_") :].replace("_", "-")
    return f"data-style-{style_name}", value


def _handle_computed(key: str, value: Any) -> tuple[str, Any]:
    """Handler for ds_computed_*."""
    computed_name = key[len("ds_computed_") :]
    data_key = _handle_computed_key(computed_name)
    # Only wrap non-empty strings in NotStr
    return data_key, _wrap_nonempty_string(value)


def _handle_cls(key: str, value: Any) -> tuple[str, Any]:
    """Handler for ds_cls - converts to data-class."""
    return "data-class", _wrap_nonempty_string(value)


def _handle_ignore(key: str, value: Any) -> tuple[str, Any]:
    """Handler for ds_ignore - skip processing element and children."""
    return "data-ignore", _convert_boolean_to_html_string(value)


def _handle_ignore_morph(key: str, value: Any) -> tuple[str, Any]:
    """Handler for ds_ignore_morph - skip morphing element during updates."""
    return "data-ignore-morph", _convert_boolean_to_html_string(value)


def _handle_preserve_attr(key: str, value: Any) -> tuple[str, Any]:
    """Handler for ds_preserve_attr - preserve attributes during morphing."""
    if isinstance(value, list):
        value = ",".join(value)
    return "data-preserve-attr", str(value)


def _handle_on_load(key: str, value: Any) -> tuple[str, Any]:
    """Handler for ds_on_load - execute expression when element loads."""
    parts = key.split("__")
    data_key = "data-on-load"
    if len(parts) > 1:
        modifiers = ".".join(parts[1:])
        data_key = f"{data_key}.{modifiers}"
    return data_key, _wrap_nonempty_string(value)


def _handle_json_signals(key: str, value: Any) -> tuple[str, Any]:
    """Handler for ds_json_signals - display signals as JSON for debugging."""
    # Handle modifiers (e.g., ds_json_signals__terse)
    parts = key.split("__")
    data_key = "data-json-signals"
    if len(parts) > 1:
        # Add modifiers (e.g., __terse becomes __terse)
        modifiers = "__".join(parts[1:])
        data_key = f"{data_key}__{modifiers}"

    if value is True:
        return data_key, True
    elif value is False:
        return data_key, "false"
    return data_key, str(value)


def _handle_on_scroll(key: str, value: Any) -> tuple[str, Any]:
    """Handler for ds_on_scroll* - generates data-scroll* attributes."""
    parts = key.split("_")

    if key == "ds_on_scroll":
        return "data-scroll", _wrap_nonempty_string(value)

    if key == "ds_on_scroll_smooth":
        return "data-scroll__smooth", _wrap_nonempty_string(value)

    if "_" in key and key.count("_") >= 3:  # ds_on_scroll_25ms
        parts = key.split("_")
        if len(parts) >= 4 and parts[-1].endswith("ms"):
            ms_value = parts[-1][:-2]
            return f"data-scroll__throttle.{ms_value}", _wrap_nonempty_string(value)

    if len(parts) >= 5 and parts[3] == "smooth" and parts[-1].endswith("ms"):
        ms_value = parts[-1][:-2]
        return f"data-scroll__smooth.throttle.{ms_value}", _wrap_nonempty_string(value)

    return "data-scroll", _wrap_nonempty_string(value)


def _handle_on_resize(key: str, value: Any) -> tuple[str, Any]:
    """Handler for ds_on_resize* - generates data-on-resize* attributes."""
    # Handle ds_on_resize__throttle_50ms -> data-on-resize__throttle.50
    if "__" in key:
        parts = key.split("__")
        if len(parts) >= 2:
            parts[0]  # ds_on_resize
            modifier_part = parts[1]  # throttle_50ms or debounce_150ms

            # Check if modifier part contains throttle/debounce and ms
            if "_" in modifier_part and modifier_part.endswith("ms"):
                modifier_parts = modifier_part.split("_")
                if len(modifier_parts) >= 2:
                    modifier_type = modifier_parts[0]  # throttle or debounce
                    ms_value = modifier_parts[1][:-2]  # Remove 'ms' suffix
                    return f"data-on-resize__{modifier_type}.{ms_value}", _wrap_nonempty_string(value)

    # Handle legacy ds_on_resize_50ms -> data-on-resize__throttle.50 (backward compatibility)
    if "_" in key and key.count("_") >= 3:  # ds_on_resize_50ms
        parts = key.split("_")
        if len(parts) >= 4 and parts[-1].endswith("ms"):
            ms_value = parts[-1][:-2]
            return f"data-on-resize__throttle.{ms_value}", _wrap_nonempty_string(value)

    return "data-on-resize", _wrap_nonempty_string(value)


def _handle_default(key: str, value: Any) -> tuple[str, Any]:
    """Default handler for simple ds_* attributes (e.g., ds_store, ds_effect)."""
    data_key = key.replace("ds_", "data-", 1).replace("_", "-")
    val = "true" if value is True else "false" if value is False else value
    # Wrap ds_effect/ds_style in NotStr, but only if non-empty
    if key in {"ds_effect", "ds_style"} and isinstance(val, str) and val:
        val = NotStr(val)
    return data_key, val


_ATTR_HANDLERS = {
    "ds_signals": _handle_signals,
    "ds_persist": _handle_persist,
    "ds_on_scroll": _handle_on_scroll,
    "ds_on_resize": _handle_on_resize,
    "ds_on_load": _handle_on_load,
    "ds_on_": _handle_on,  # Generic handler must come after specific ones
    "ds_attr_": _handle_attr,
    "ds_style_": _handle_style,
    "ds_computed_": _handle_computed,
    "ds_cls": _handle_cls,
    "ds_ignore": _handle_ignore,
    "ds_ignore_morph": _handle_ignore_morph,
    "ds_preserve_attr": _handle_preserve_attr,
    "ds_json_signals": _handle_json_signals,
}

_VALID_SIGNAL_NAME_REGEX = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_-]*$")


def _validate_signal_name(signal_name: str) -> None:
    """Raise ValueError if a signal name is invalid."""
    if not _VALID_SIGNAL_NAME_REGEX.match(signal_name):
        raise ValueError(
            f"Invalid signal name '{signal_name}'. Signal names must start with a letter "
            "or underscore, and contain only letters, numbers, underscores, or dashes."
        )


def _process_persist_value(value: str | bool) -> str:
    """Process ds_persist value according to hybrid API syntax.

    Supported formats:
    - True -> persist all signals in element scope
    - False -> disable persistence
    - "" (empty string) -> persist all signals in element scope
    - "*" -> persist all signals (wildcard)
    - "signal1,signal2" -> persist specific signals by name
    """
    if value is True:
        return "*"
    if value is False or not isinstance(value, str):
        return "false"

    stripped_value = value.strip()
    if not stripped_value:
        return "*"

    # Special case for wildcard
    if stripped_value == "*":
        return "*"

    # Parse comma-separated signal names
    signal_names = [s for s in (part.strip() for part in stripped_value.split(",")) if s]
    for signal_name in signal_names:
        _validate_signal_name(signal_name)

    return ",".join(signal_names)


def _handle_event_key(event_part: str) -> str:
    """Transform ds_on_* event keys using clear rules."""
    # Rule 1: Double underscore -> dot notation
    if "__" in event_part:
        base_event, modifier = event_part.split("__", 1)
        return f"data-on-{base_event}.{modifier}"

    # Rule 2: No underscores -> simple event
    if "_" not in event_part:
        return f"data-on-{event_part}"

    parts = event_part.split("_")
    base_event = parts[0]

    # Rule 3: Timing modifiers (250ms -> .250ms)
    if len(parts) >= 2 and parts[-1].endswith("ms"):
        ms_part = parts[-1]
        if len(parts) == 2:
            return f"data-on-{base_event}.{ms_part}"
        middle_parts = "_".join(parts[1:-1])
        return f"data-on-{base_event}_{middle_parts}.{ms_part}"

    # Rule 4: Special events keep underscores as dots
    if base_event in {"intersect", "interval"}:
        modifier = "_".join(parts[1:])
        return f"data-on-{base_event}.{modifier}"

    # Rule 5: Default - convert underscores to dashes
    return f"data-on-{event_part.replace('_', '-')}"


def _handle_computed_key(computed_name: str) -> str:
    """Transform ds_computed_* keys to data-computed-* format."""
    if "__case" in computed_name:
        signal_name, modifier = computed_name.split("__case", 1)
        signal_name_kebab = _camel_to_kebab(signal_name)
        modifier = modifier.replace("_", ".")
        return f"data-computed-{signal_name_kebab}__case{modifier}"

    return f"data-computed-{_camel_to_kebab(computed_name)}"
