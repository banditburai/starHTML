"""Type definitions and protocols for StarHTML."""

from typing import Any, Literal, Protocol, TypeVar

from fastcore.xml import FT

from starhtml.datastar import DatastarAttr

# Core HTML content types
HTMLContent = str | int | float | FT | DatastarAttr | None
HTMLChildren = HTMLContent | tuple[HTMLContent, ...] | list[HTMLContent]

# CSS and style types
CSSValue = str | int | float | None
CSSUnit = Literal["px", "em", "rem", "%", "vh", "vw", "pt", "cm", "mm", "in"]

# Input types
InputType = Literal[
    "button",
    "checkbox",
    "color",
    "date",
    "datetime-local",
    "email",
    "file",
    "hidden",
    "image",
    "month",
    "number",
    "password",
    "radio",
    "range",
    "reset",
    "search",
    "submit",
    "tel",
    "text",
    "time",
    "url",
    "week",
]

# Button types
ButtonType = Literal["button", "submit", "reset"]

# Form method types
FormMethod = Literal["get", "post", "dialog"]

# Target types for links and forms
TargetType = Literal["_blank", "_self", "_parent", "_top"]

# Autocomplete types
AutocompleteType = Literal["on", "off"] | str

# Crossorigin types
CrossoriginType = Literal["anonymous", "use-credentials"]

# Loading types for images and iframes
LoadingType = Literal["lazy", "eager"]

# Referrer policy types
ReferrerPolicyType = Literal[
    "no-referrer",
    "no-referrer-when-downgrade",
    "origin",
    "origin-when-cross-origin",
    "same-origin",
    "strict-origin",
    "strict-origin-when-cross-origin",
    "unsafe-url",
]

# Protocol for HTML element callables
T = TypeVar("T", bound="HTMLElement")


class HTMLElement(Protocol):
    """Protocol for HTML element factory functions."""

    def __call__(
        self,
        *children: HTMLContent,
        id: str | None = None,
        cls: str | None = None,
        style: CSSValue | None = None,
        **attrs: Any,
    ) -> FT: ...


class FormElement(HTMLElement, Protocol):
    """Protocol for form-related HTML elements."""

    def __call__(
        self,
        *children: HTMLContent,
        name: str | None = None,
        value: str | None = None,
        id: str | None = None,
        cls: str | None = None,
        style: CSSValue | None = None,
        **attrs: Any,
    ) -> FT: ...


class MediaElement(HTMLElement, Protocol):
    """Protocol for media HTML elements (img, video, audio)."""

    def __call__(
        self,
        src: str | None = None,
        alt: str | None = None,
        width: int | str | None = None,
        height: int | str | None = None,
        id: str | None = None,
        cls: str | None = None,
        style: CSSValue | None = None,
        **attrs: Any,
    ) -> FT: ...


# Event handler types
EventHandler = str | None


# Common HTML attributes type
class HTMLAttributes:
    """Common HTML attributes shared by most elements."""

    id: str | None
    cls: str | None  # 'class' is a reserved keyword in Python
    style: CSSValue | None
    title: str | None
    lang: str | None
    dir: Literal["ltr", "rtl", "auto"] | None
    tabindex: int | None
    hidden: bool | None
    contenteditable: bool | Literal["true", "false", "inherit"] | None
    draggable: bool | Literal["true", "false", "auto"] | None
    spellcheck: bool | Literal["true", "false"] | None
    translate: Literal["yes", "no"] | bool | None

    # ARIA attributes
    role: str | None
    aria_label: str | None
    aria_labelledby: str | None
    aria_describedby: str | None
    aria_hidden: bool | None

    # Data attributes (data-*)
    data: dict[str, Any] | None

    # Event handlers
    onclick: EventHandler | None
    onchange: EventHandler | None
    oninput: EventHandler | None
    onsubmit: EventHandler | None
    onfocus: EventHandler | None
    onblur: EventHandler | None
    onkeydown: EventHandler | None
    onkeyup: EventHandler | None
    onmouseover: EventHandler | None
    onmouseout: EventHandler | None
    onmousedown: EventHandler | None
    onmouseup: EventHandler | None
    onmousemove: EventHandler | None
