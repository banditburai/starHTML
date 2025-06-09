"""Simple extensions to standard HTML components, such as adding sensible defaults"""

from dataclasses import dataclass, asdict
from typing import Any

from fastcore.utils import *
from fastcore.xtras import partial_format
from fastcore.xml import *
from fastcore.meta import use_kwargs, delegates
from .core import *
from .components import *

__all__ = [
    "A",
    "AX",
    "Form",
    "Hidden",
    "CheckboxX",
    "Script",
    "Style",
    "double_braces",
    "undouble_braces",
    "loose_format",
    "ScriptX",
    "replace_css_vars",
    "StyleX",
    "Nbsp",
    "run_js",
    "DatastarOn",
    "jsd",
    "Fragment",
    "Socials",
    "YouTubeEmbed",
    "Favicon",
    "with_sid",
]


@delegates(ft_datastar, keep=True)
def A(*c, get=None, target_id=None, href="#", **kwargs) -> FT:
    "An A tag; `href` defaults to '#' for more concise use with Datastar"
    if get:
        kwargs["data_on_click"] = f"@get('{get}')"
    return ft_datastar("a", *c, href=href, **kwargs)


@delegates(ft_datastar, keep=True)
def AX(txt, get=None, target_id=None, href="#", **kwargs) -> FT:
    "An A tag with just one text child, allowing get and target_id to be positional params"
    if get:
        kwargs["data_on_click"] = f"@get('{get}')"
    return ft_datastar("a", txt, href=href, **kwargs)


@delegates(ft_datastar, keep=True)
def Form(*c, enctype="multipart/form-data", **kwargs) -> FT:
    "A Form tag; identical to plain `ft_datastar` version except default `enctype='multipart/form-data'`"
    return ft_datastar("form", *c, enctype=enctype, **kwargs)


@delegates(ft_datastar, keep=True)
def Hidden(value: Any = "", id: Any = None, **kwargs) -> FT:
    "An Input of type 'hidden'"
    return Input(type="hidden", value=value, id=id, **kwargs)


@delegates(ft_datastar, keep=True)
def CheckboxX(checked: bool = False, label=None, value="1", id=None, name=None, **kwargs) -> FT:
    "A Checkbox optionally inside a Label, preceded by a `Hidden` with matching name"
    if id and not name:
        name = id
    if not checked:
        checked = None
    res = Input(type="checkbox", id=id, name=name, checked=checked, value=value, **kwargs)
    if label:
        res = Label(res, label)
    return Hidden(name=name, skip=True, value=""), res


@delegates(ft_datastar, keep=True)
def Script(code: str = "", **kwargs) -> FT:
    "A Script tag that doesn't escape its code and supports Datastar attributes"
    return ft_datastar("script", NotStr(code), **kwargs)


@delegates(ft_html, keep=True)
def Style(*c, **kwargs) -> FT:
    "A Style tag that doesn't escape its code"
    return ft_html("style", map(NotStr, c), **kwargs)


def double_braces(s):
    "Convert single braces to double braces if next to special chars or newline"
    s = re.sub(r'{(?=[\s:;\'"]|$)', "{{", s)
    return re.sub(r'(^|[\s:;\'"])}', r"\1}}", s)


def undouble_braces(s):
    "Convert double braces to single braces if next to special chars or newline"
    s = re.sub(r'\{\{(?=[\s:;\'"]|$)', "{", s)
    return re.sub(r'(^|[\s:;\'"])\}\}', r"\1}", s)


def loose_format(s, **kw):
    "String format `s` using `kw`, without being strict about braces outside of template params"
    if not kw:
        return s
    return undouble_braces(partial_format(double_braces(s), **kw)[0])


def ScriptX(
    fname,
    src=None,
    nomodule=None,
    type=None,
    _async=None,
    defer=None,
    charset=None,
    crossorigin=None,
    integrity=None,
    **kw,
):
    "A `script` element with contents read from `fname`"
    s = loose_format(Path(fname).read_text(), **kw)
    return Script(
        s,
        src=src,
        nomodule=nomodule,
        type=type,
        _async=_async,
        defer=defer,
        charset=charset,
        crossorigin=crossorigin,
        integrity=integrity,
    )


def replace_css_vars(css, pre="tpl", **kwargs):
    "Replace `var(--)` CSS variables with `kwargs` if name prefix matches `pre`"
    if not kwargs:
        return css

    def replace_var(m):
        var_name = m.group(1).replace("-", "_")
        return kwargs.get(var_name, m.group(0))

    return re.sub(rf"var\(--{pre}-([\w-]+)\)", replace_var, css)


def StyleX(fname, **kw):
    "A `style` element with contents read from `fname` and variables replaced from `kw`"
    s = Path(fname).read_text()
    attrs = ["type", "media", "scoped", "title", "nonce", "integrity", "crossorigin"]
    sty_kw = {k: kw.pop(k) for k in attrs if k in kw}
    return Style(replace_css_vars(s, **kw), **sty_kw)


def Nbsp():
    "A non-breaking space"
    return Safe("&nbsp;")


def run_js(js, id=None, **kw):
    "Run `js` script, auto-generating `id` based on name of caller if needed, and js-escaping any `kw` params"
    if not id:
        id = sys._getframe(1).f_code.co_name
    kw = {k: dumps(v) for k, v in kw.items()}
    return Script(js.format(**kw), id=id)


def DatastarOn(eventname: str, code: str):
    return Script(
        """domReadyExecute(function() {
document.body.addEventListener("datastar:%s", function(event) { %s })
})"""
        % (eventname, code)
    )


def jsd(org, repo, root, path, prov="gh", typ="script", ver=None, esm=False, **kwargs) -> FT:
    "jsdelivr `Script` or CSS `Link` tag, or URL"
    ver = "@" + ver if ver else ""
    s = f"https://cdn.jsdelivr.net/{prov}/{org}/{repo}{ver}/{root}/{path}"
    if esm:
        s += "/+esm"
    return (
        Script(src=s, **kwargs) if typ == "script" else Link(rel="stylesheet", href=s, **kwargs) if typ == "css" else s
    )


class Fragment(FT):
    "An empty tag, used as a container"

    def __init__(self, *c):
        super().__init__("", c, {}, void_=True)


def Socials(
    title, site_name, description, image, url=None, w=1200, h=630, twitter_site=None, creator=None, card="summary"
):
    "OG and Twitter social card headers"
    if not url:
        url = site_name
    if not url.startswith("http"):
        url = f"https://{url}"
    if not image.startswith("http"):
        image = f"{url}{image}"
    res = [
        Meta(property="og:image", content=image),
        Meta(property="og:site_name", content=site_name),
        Meta(property="og:image:type", content="image/png"),
        Meta(property="og:image:width", content=w),
        Meta(property="og:image:height", content=h),
        Meta(property="og:type", content="website"),
        Meta(property="og:url", content=url),
        Meta(property="og:title", content=title),
        Meta(property="og:description", content=description),
        Meta(name="twitter:image", content=image),
        Meta(name="twitter:card", content=card),
        Meta(name="twitter:title", content=title),
        Meta(name="twitter:description", content=description),
    ]
    if twitter_site is not None:
        res.append(Meta(name="twitter:site", content=twitter_site))
    if creator is not None:
        res.append(Meta(name="twitter:creator", content=creator))
    return tuple(res)


def YouTubeEmbed(
    video_id: str,
    *,
    width: int = 560,
    height: int = 315,
    start_time: int = 0,
    no_controls: bool = False,
    title: str = "YouTube video player",
    cls: str = "",
    **kwargs,
):
    """Embed a YouTube video"""
    if not video_id or not isinstance(video_id, str):
        raise ValueError("A valid YouTube video ID is required")
    params = []
    if start_time > 0:
        params.append(f"start={start_time}")
    if no_controls:
        params.append("controls=0")
    query_string = "?" + "&".join(params) if params else ""
    print(f"https://www.youtube.com/embed/{video_id}{query_string}")
    return Div(
        Iframe(
            width=width,
            height=height,
            src=f"https://www.youtube.com/embed/{video_id}{query_string}",
            title=title,
            frameborder="0",
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share",
            referrerpolicy="strict-origin-when-cross-origin",
            allowfullscreen="",
            **kwargs,
        ),
        cls=cls,
    )


def Favicon(light_icon, dark_icon):
    "Light and dark favicon headers"
    return (
        Link(rel="icon", type="image/x-ico", href=light_icon, media="(prefers-color-scheme: light)"),
        Link(rel="icon", type="image/x-ico", href=dark_icon, media="(prefers-color-scheme: dark)"),
    )


def with_sid(app, dest, path="/"):
    @app.route(path)
    def get():
        return Div(data_on_load=f'@get("{dest}")', data_swap="outerHTML")
