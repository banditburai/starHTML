"""Type stubs for StarHTML tag functions."""

from typing import Any, Literal

from fastcore.xml import FT

from .tags import (
    _HTML_TAG_NAMES as _HTML_TAG_NAMES,
)
from .tags import (
    _SVG_TAG_NAMES as _SVG_TAG_NAMES,
)

# Re-export the actual implementations
from .tags import (
    _create_tag_factory as _create_tag_factory,
)
from .types import (
    AutocompleteType,
    ButtonType,
    CrossoriginType,
    CSSValue,
    EventHandler,
    FormMethod,
    HTMLContent,
    InputType,
    LoadingType,
    ReferrerPolicyType,
    TargetType,
)

# HTML Elements with proper type signatures

# Text content elements
def A(
    *children: HTMLContent,
    href: str | None = None,
    target: TargetType | None = None,
    rel: str | None = None,
    download: bool | str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Abbr(
    *children: HTMLContent,
    title: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Address(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Area(
    alt: str | None = None,
    coords: str | None = None,
    shape: Literal["rect", "circle", "poly", "default"] | None = None,
    href: str | None = None,
    target: TargetType | None = None,
    id: str | None = None,
    cls: str | None = None,
    **attrs: Any,
) -> FT: ...
def Article(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Aside(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Audio(
    *children: HTMLContent,
    src: str | None = None,
    controls: bool | None = None,
    autoplay: bool | None = None,
    loop: bool | None = None,
    muted: bool | None = None,
    preload: Literal["none", "metadata", "auto"] | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def B(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Base(href: str | None = None, target: TargetType | None = None, **attrs: Any) -> FT: ...
def Bdi(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Bdo(
    *children: HTMLContent,
    dir: Literal["ltr", "rtl"] | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Blockquote(
    *children: HTMLContent,
    cite: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Body(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Br(id: str | None = None, cls: str | None = None, **attrs: Any) -> FT: ...
def Button(
    *children: HTMLContent,
    type: ButtonType | None = None,
    name: str | None = None,
    value: str | None = None,
    disabled: bool | None = None,
    form: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    onclick: EventHandler | None = None,
    **attrs: Any,
) -> FT: ...
def Canvas(
    *children: HTMLContent,
    width: int | str | None = None,
    height: int | str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Caption(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Cite(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Code(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Col(
    span: int | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Colgroup(
    *children: HTMLContent,
    span: int | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Data(
    *children: HTMLContent,
    value: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Datalist(*children: HTMLContent, id: str | None = None, cls: str | None = None, **attrs: Any) -> FT: ...
def Dd(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Del(
    *children: HTMLContent,
    cite: str | None = None,
    datetime: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Details(
    *children: HTMLContent,
    open: bool | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Dfn(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Dialog(
    *children: HTMLContent,
    open: bool | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Div(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Dl(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Dt(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Em(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Embed(
    src: str | None = None,
    type: str | None = None,
    width: int | str | None = None,
    height: int | str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Fencedframe(
    *children: HTMLContent,
    src: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Fieldset(
    *children: HTMLContent,
    disabled: bool | None = None,
    form: str | None = None,
    name: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Figcaption(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Figure(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Footer(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Form(
    *children: HTMLContent,
    action: str | None = None,
    method: FormMethod | None = None,
    enctype: str | None = None,
    name: str | None = None,
    target: TargetType | None = None,
    autocomplete: AutocompleteType | None = None,
    novalidate: bool | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    onsubmit: EventHandler | None = None,
    **attrs: Any,
) -> FT: ...
def H1(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def H2(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def H3(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def H4(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def H5(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def H6(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Head(*children: HTMLContent, **attrs: Any) -> FT: ...
def Header(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Hgroup(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Hr(id: str | None = None, cls: str | None = None, style: CSSValue | None = None, **attrs: Any) -> FT: ...
def Html(*children: HTMLContent, lang: str | None = None, **attrs: Any) -> FT: ...
def I(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Iframe(
    src: str | None = None,
    srcdoc: str | None = None,
    width: int | str | None = None,
    height: int | str | None = None,
    allow: str | None = None,
    allowfullscreen: bool | None = None,
    loading: LoadingType | None = None,
    name: str | None = None,
    referrerpolicy: ReferrerPolicyType | None = None,
    sandbox: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Img(
    src: str | None = None,
    alt: str | None = None,
    width: int | str | None = None,
    height: int | str | None = None,
    loading: LoadingType | None = None,
    crossorigin: CrossoriginType | None = None,
    decoding: Literal["sync", "async", "auto"] | None = None,
    referrerpolicy: ReferrerPolicyType | None = None,
    sizes: str | None = None,
    srcset: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Input(
    type: InputType | None = None,
    name: str | None = None,
    value: str | None = None,
    placeholder: str | None = None,
    required: bool | None = None,
    disabled: bool | None = None,
    readonly: bool | None = None,
    checked: bool | None = None,
    min: str | int | float | None = None,
    max: str | int | float | None = None,
    step: str | int | float | None = None,
    pattern: str | None = None,
    maxlength: int | None = None,
    minlength: int | None = None,
    autocomplete: AutocompleteType | None = None,
    autofocus: bool | None = None,
    form: str | None = None,
    list: str | None = None,
    multiple: bool | None = None,
    accept: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    onchange: EventHandler | None = None,
    oninput: EventHandler | None = None,
    **attrs: Any,
) -> FT: ...
def Ins(
    *children: HTMLContent,
    cite: str | None = None,
    datetime: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Kbd(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Label(
    *children: HTMLContent,
    for_: str | None = None,  # 'for' is a reserved keyword
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Legend(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Li(
    *children: HTMLContent,
    value: int | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Link(
    href: str | None = None,
    rel: str | None = None,
    type: str | None = None,
    media: str | None = None,
    as_: str | None = None,  # 'as' is a reserved keyword
    crossorigin: CrossoriginType | None = None,
    integrity: str | None = None,
    referrerpolicy: ReferrerPolicyType | None = None,
    sizes: str | None = None,
    **attrs: Any,
) -> FT: ...
def Main(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Map(
    *children: HTMLContent,
    name: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Mark(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Menu(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Meta(
    charset: str | None = None,
    content: str | None = None,
    http_equiv: str | None = None,
    name: str | None = None,
    **attrs: Any,
) -> FT: ...
def Meter(
    *children: HTMLContent,
    value: int | float | None = None,
    min: int | float | None = None,
    max: int | float | None = None,
    low: int | float | None = None,
    high: int | float | None = None,
    optimum: int | float | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Nav(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Noscript(*children: HTMLContent, **attrs: Any) -> FT: ...
def Object(
    *children: HTMLContent,
    data: str | None = None,
    type: str | None = None,
    width: int | str | None = None,
    height: int | str | None = None,
    name: str | None = None,
    form: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Ol(
    *children: HTMLContent,
    reversed: bool | None = None,
    start: int | None = None,
    type: Literal["1", "a", "A", "i", "I"] | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Optgroup(*children: HTMLContent, disabled: bool | None = None, label: str | None = None, **attrs: Any) -> FT: ...
def Option(
    *children: HTMLContent,
    disabled: bool | None = None,
    label: str | None = None,
    selected: bool | None = None,
    value: str | None = None,
    **attrs: Any,
) -> FT: ...
def Output(
    *children: HTMLContent,
    for_: str | None = None,  # 'for' is a reserved keyword
    form: str | None = None,
    name: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def P(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Picture(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def PortalExperimental(
    *children: HTMLContent,
    src: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Pre(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Progress(
    *children: HTMLContent,
    value: int | float | None = None,
    max: int | float | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Q(
    *children: HTMLContent,
    cite: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Rp(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Rt(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Ruby(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def S(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Samp(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Script(
    *children: HTMLContent,
    src: str | None = None,
    type: str | None = None,
    async_: bool | None = None,  # 'async' is a reserved keyword
    defer: bool | None = None,
    crossorigin: CrossoriginType | None = None,
    integrity: str | None = None,
    nomodule: bool | None = None,
    referrerpolicy: ReferrerPolicyType | None = None,
    **attrs: Any,
) -> FT: ...
def Search(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Section(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Select(
    *children: HTMLContent,
    name: str | None = None,
    size: int | None = None,
    multiple: bool | None = None,
    disabled: bool | None = None,
    required: bool | None = None,
    autofocus: bool | None = None,
    autocomplete: AutocompleteType | None = None,
    form: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    onchange: EventHandler | None = None,
    **attrs: Any,
) -> FT: ...
def Slot(
    *children: HTMLContent,
    name: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Small(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Source(
    src: str | None = None,
    type: str | None = None,
    media: str | None = None,
    sizes: str | None = None,
    srcset: str | None = None,
    **attrs: Any,
) -> FT: ...
def Span(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Strong(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Style(*children: HTMLContent, media: str | None = None, **attrs: Any) -> FT: ...
def Sub(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Summary(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Sup(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Table(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Tbody(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Td(
    *children: HTMLContent,
    colspan: int | None = None,
    rowspan: int | None = None,
    headers: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Template(*children: HTMLContent, id: str | None = None, **attrs: Any) -> FT: ...
def Textarea(
    *children: HTMLContent,
    name: str | None = None,
    rows: int | None = None,
    cols: int | None = None,
    disabled: bool | None = None,
    readonly: bool | None = None,
    required: bool | None = None,
    placeholder: str | None = None,
    maxlength: int | None = None,
    minlength: int | None = None,
    autocomplete: AutocompleteType | None = None,
    autofocus: bool | None = None,
    form: str | None = None,
    wrap: Literal["hard", "soft"] | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    onchange: EventHandler | None = None,
    oninput: EventHandler | None = None,
    **attrs: Any,
) -> FT: ...
def Tfoot(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Th(
    *children: HTMLContent,
    colspan: int | None = None,
    rowspan: int | None = None,
    headers: str | None = None,
    scope: Literal["row", "col", "rowgroup", "colgroup"] | None = None,
    abbr: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Thead(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Time(
    *children: HTMLContent,
    datetime: str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Title(*children: HTMLContent, **attrs: Any) -> FT: ...
def Tr(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Track(
    src: str | None = None,
    kind: Literal["subtitles", "captions", "descriptions", "chapters", "metadata"] | None = None,
    label: str | None = None,
    srclang: str | None = None,
    default: bool | None = None,
    **attrs: Any,
) -> FT: ...
def U(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Ul(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Var(
    *children: HTMLContent,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Video(
    *children: HTMLContent,
    src: str | None = None,
    poster: str | None = None,
    width: int | str | None = None,
    height: int | str | None = None,
    controls: bool | None = None,
    autoplay: bool | None = None,
    loop: bool | None = None,
    muted: bool | None = None,
    preload: Literal["none", "metadata", "auto"] | None = None,
    crossorigin: CrossoriginType | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Wbr(**attrs: Any) -> FT: ...

# SVG Elements
def Svg(
    *children: HTMLContent,
    width: int | str | None = None,
    height: int | str | None = None,
    viewBox: str | None = None,
    xmlns: str | None = None,
    fill: str | None = None,
    stroke: str | None = None,
    stroke_width: int | str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def G(
    *children: HTMLContent,
    transform: str | None = None,
    fill: str | None = None,
    stroke: str | None = None,
    stroke_width: int | str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Rect(
    x: int | str | None = None,
    y: int | str | None = None,
    width: int | str | None = None,
    height: int | str | None = None,
    rx: int | str | None = None,
    ry: int | str | None = None,
    fill: str | None = None,
    stroke: str | None = None,
    stroke_width: int | str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Circle(
    cx: int | str | None = None,
    cy: int | str | None = None,
    r: int | str | None = None,
    fill: str | None = None,
    stroke: str | None = None,
    stroke_width: int | str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Ellipse(
    cx: int | str | None = None,
    cy: int | str | None = None,
    rx: int | str | None = None,
    ry: int | str | None = None,
    fill: str | None = None,
    stroke: str | None = None,
    stroke_width: int | str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Line(
    x1: int | str | None = None,
    y1: int | str | None = None,
    x2: int | str | None = None,
    y2: int | str | None = None,
    stroke: str | None = None,
    stroke_width: int | str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Polyline(
    points: str | None = None,
    fill: str | None = None,
    stroke: str | None = None,
    stroke_width: int | str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Polygon(
    points: str | None = None,
    fill: str | None = None,
    stroke: str | None = None,
    stroke_width: int | str | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def Text(
    *children: HTMLContent,
    x: int | str | None = None,
    y: int | str | None = None,
    dx: int | str | None = None,
    dy: int | str | None = None,
    rotate: str | None = None,
    textLength: int | str | None = None,
    lengthAdjust: Literal["spacing", "spacingAndGlyphs"] | None = None,
    fill: str | None = None,
    stroke: str | None = None,
    stroke_width: int | str | None = None,
    font_family: str | None = None,
    font_size: int | str | None = None,
    font_weight: int | str | None = None,
    text_anchor: Literal["start", "middle", "end"] | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...
def SvgPath(
    d: str | None = None,
    fill: str | None = None,
    stroke: str | None = None,
    stroke_width: int | str | None = None,
    stroke_linecap: Literal["butt", "round", "square"] | None = None,
    stroke_linejoin: Literal["miter", "round", "bevel"] | None = None,
    fill_rule: Literal["nonzero", "evenodd"] | None = None,
    id: str | None = None,
    cls: str | None = None,
    style: CSSValue | None = None,
    **attrs: Any,
) -> FT: ...

# Additional SVG elements (simplified signatures)
def AltGlyph(*children: HTMLContent, **attrs: Any) -> FT: ...
def AltGlyphDef(*children: HTMLContent, **attrs: Any) -> FT: ...
def AltGlyphItem(*children: HTMLContent, **attrs: Any) -> FT: ...
def Animate(**attrs: Any) -> FT: ...
def AnimateColor(**attrs: Any) -> FT: ...
def AnimateMotion(**attrs: Any) -> FT: ...
def AnimateTransform(**attrs: Any) -> FT: ...
def ClipPath(*children: HTMLContent, **attrs: Any) -> FT: ...
def Color_profile(**attrs: Any) -> FT: ...
def Cursor(**attrs: Any) -> FT: ...
def Defs(*children: HTMLContent, **attrs: Any) -> FT: ...
def Desc(*children: HTMLContent, **attrs: Any) -> FT: ...

# SVG Filter elements
def FeBlend(**attrs: Any) -> FT: ...
def FeColorMatrix(**attrs: Any) -> FT: ...
def FeComponentTransfer(**attrs: Any) -> FT: ...
def FeComposite(**attrs: Any) -> FT: ...
def FeConvolveMatrix(**attrs: Any) -> FT: ...
def FeDiffuseLighting(**attrs: Any) -> FT: ...
def FeDisplacementMap(**attrs: Any) -> FT: ...
def FeDistantLight(**attrs: Any) -> FT: ...
def FeFlood(**attrs: Any) -> FT: ...
def FeFuncA(**attrs: Any) -> FT: ...
def FeFuncB(**attrs: Any) -> FT: ...
def FeFuncG(**attrs: Any) -> FT: ...
def FeFuncR(**attrs: Any) -> FT: ...
def FeGaussianBlur(**attrs: Any) -> FT: ...
def FeImage(**attrs: Any) -> FT: ...
def FeMerge(**attrs: Any) -> FT: ...
def FeMergeNode(**attrs: Any) -> FT: ...
def FeMorphology(**attrs: Any) -> FT: ...
def FeOffset(**attrs: Any) -> FT: ...
def FePointLight(**attrs: Any) -> FT: ...
def FeSpecularLighting(**attrs: Any) -> FT: ...
def FeSpotLight(**attrs: Any) -> FT: ...
def FeTile(**attrs: Any) -> FT: ...
def FeTurbulence(**attrs: Any) -> FT: ...
def Filter(*children: HTMLContent, **attrs: Any) -> FT: ...

# SVG Font elements
def Font(**attrs: Any) -> FT: ...
def Font_face(**attrs: Any) -> FT: ...
def Font_face_format(**attrs: Any) -> FT: ...
def Font_face_name(**attrs: Any) -> FT: ...
def Font_face_src(**attrs: Any) -> FT: ...
def Font_face_uri(**attrs: Any) -> FT: ...
def ForeignObject(*children: HTMLContent, **attrs: Any) -> FT: ...
def Glyph(**attrs: Any) -> FT: ...
def GlyphRef(**attrs: Any) -> FT: ...
def Hkern(**attrs: Any) -> FT: ...

# SVG Gradient and other elements
def Image(**attrs: Any) -> FT: ...
def LinearGradient(**attrs: Any) -> FT: ...
def Marker(**attrs: Any) -> FT: ...
def Mask(*children: HTMLContent, **attrs: Any) -> FT: ...
def Metadata(*children: HTMLContent, **attrs: Any) -> FT: ...
def Missing_glyph(**attrs: Any) -> FT: ...
def Mpath(**attrs: Any) -> FT: ...
def Pattern(*children: HTMLContent, **attrs: Any) -> FT: ...
def RadialGradient(**attrs: Any) -> FT: ...
def Set(**attrs: Any) -> FT: ...
def Stop(**attrs: Any) -> FT: ...
def Switch(*children: HTMLContent, **attrs: Any) -> FT: ...
def Symbol(*children: HTMLContent, **attrs: Any) -> FT: ...
def TextPath(*children: HTMLContent, **attrs: Any) -> FT: ...
def Tref(*children: HTMLContent, **attrs: Any) -> FT: ...
def Tspan(*children: HTMLContent, **attrs: Any) -> FT: ...
def Use(**attrs: Any) -> FT: ...
def View(**attrs: Any) -> FT: ...
def Vkern(**attrs: Any) -> FT: ...

# For any dynamically created tags not in the standard lists
def __getattr__(name: str) -> Any: ...
