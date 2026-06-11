"""Patch definitions for vendored Datastar (durable stable-landmark anchoring).

Datastar ships a minified bundle whose single-char identifiers are reassigned on
every release, so patches anchored on those names break on each upgrade. Instead,
each patch first *captures* the few volatile tokens it needs (scan-fn name, event
consts, handler vars, the `action` export alias) by matching STABLE string/
structural landmarks — `document.documentElement,t=!0)=>{`, `n.has("outside")`,
`"kebab"`, `e.style.display==="none"`, `export{… as action}` — none of which
changed across 1.0.1 → 1.0.2. The captured names fill `«token»` placeholders in
the search/replace operations (guillemets never occur in the bundle, so the JS
braces need no escaping). The same definitions therefore patch multiple Datastar
versions unchanged. `apply_patch` still requires each search to occur exactly
once, so a genuine structural change upstream fails loudly instead of silently
mis-patching.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class PatchDef:
    name: str
    captures: dict[str, str]  # token -> regex with exactly one capturing group
    operations: list[tuple[str, str]]  # (search, replace), using «token» placeholders
    markers: list[str] = field(default_factory=list)  # stable post-patch literals


PATCHED_HEADER = "// Datastar v{version} (StarHTML patched: shadow-dom-scan, outside-race-fix)"

PATCHES: list[PatchDef] = [
    PatchDef(
        name="shadow-dom-scan",
        captures={
            "fn": r"(\w+)=\(e=document\.documentElement,t=!0\)=>\{",  # scan function
            "chk": r"=\(e=document\.documentElement,t=!0\)=>\{(\w+)\(e\)&&",  # connected-check
            "scan": r"=>\{\w+\(e\)&&(\w+)\(\[e\],!0\),",  # attribute-scan helper
            "act": r"export\{(\w+) as action",  # `action` export alias
        },
        operations=[
            # Add a third filter arg `n` (default keep upstream behavior) threaded to both
            # scan calls, so explicit shadow-root scans can bind all loaded plugins.
            (
                '«fn»=(e=document.documentElement,t=!0)=>{«chk»(e)&&«scan»([e],!0),«scan»(e.querySelectorAll("*"),!0),',
                '«fn»=(e=document.documentElement,t=!0,n=!0)=>{«chk»(e)&&«scan»([e],n),«scan»(e.querySelectorAll("*"),n),',
            ),
            # StarElements' `datastar:scan` event has no upstream listener; add one that
            # scans the provided (shadow) root with no plugin filter.
            (
                "export{«act» as action",
                'document.addEventListener("datastar:scan",e=>{let t=e.detail?.root;t&&«fn»(t.shadowRoot||t,!0,!1)});'
                "export{«act» as action",
            ),
        ],
        markers=[
            'e.querySelectorAll("*"),n),',
            'document.addEventListener("datastar:scan",e=>{let t=e.detail',
        ],
    ),
    PatchDef(
        name="outside-race-fix",
        captures={
            "kebab": r'let o=(\w+)\(t,n,"kebab"\)',  # event-name kebab helper
            "saved": r'if\(n\.has\("outside"\)\)\{s=document;let (\w+)=i;',  # saved inner handler
            "ev": r"\}\((o===\w+\|\|o===\w+)\)&&\(s=document\);",  # focus/blur event consts
            "listener": r"s\.removeEventListener\(o,(\w+),a\)\}\}\}\);",  # registered listener
        },
        operations=[
            # Suppress spurious `outside` events during the gesture that opened the element:
            # a MutationObserver+rAF flag (cross-event) and a capture-phase display:none
            # snapshot (same-event). `d` tears both down on listener removal.
            (
                'let o=«kebab»(t,n,"kebab"),a={capture:n.has("capture"),passive:n.has("passive"),once:n.has("once")};'
                'if(n.has("outside")){s=document;let «saved»=i;i=u=>{e.contains(u?.target)||«saved»(u)}}'
                "(«ev»)&&(s=document);",
                'let o=«kebab»(t,n,"kebab"),a={capture:n.has("capture"),passive:n.has("passive"),once:n.has("once")},d;'
                'if(n.has("outside")){s=document;let «saved»=i,u=!1,'
                "f=new MutationObserver(()=>{u=!0;requestAnimationFrame(()=>{u=!1})});"
                'f.observe(e,{attributeFilter:["style"]});'
                'let g=!1,h=()=>{g=e.style.display==="none"};'
                "document.addEventListener(o,h,!0);"
                "i=p=>{u||g||e.contains(p?.target)||«saved»(p)};"
                "d=()=>{f.disconnect();document.removeEventListener(o,h,!0)}}"
                "(«ev»)&&(s=document);",
            ),
            (
                "s.removeEventListener(o,«listener»,a)}}});",
                "s.removeEventListener(o,«listener»,a);d?.()}}});",
            ),
        ],
        markers=[
            "requestAnimationFrame(()=>{u=!1})",
            'e.style.display==="none"',
            'once:n.has("once")},d;if(n.has("outside")',
        ],
    ),
]


def _resolve_captures(content: str, patch: PatchDef) -> dict[str, str]:
    """Extract the patch's volatile tokens from stable landmarks; each must be unique."""
    caps: dict[str, str] = {}
    for name, pattern in patch.captures.items():
        found = re.findall(pattern, content)
        if len(found) != 1:
            raise ValueError(
                f"Patch '{patch.name}': capture {name!r} matched {len(found)} times (expected 1): /{pattern}/"
            )
        caps[name] = found[0]
    return caps


def _fill(template: str, caps: dict[str, str]) -> str:
    for name, value in caps.items():
        template = template.replace(f"«{name}»", value)
    return template


def apply_patch(content: str, patch: PatchDef) -> str:
    """Idempotent — skips if already applied (all markers present)."""
    if patch.markers and all(marker in content for marker in patch.markers):
        return content
    caps = _resolve_captures(content, patch)
    for search_t, replace_t in patch.operations:
        search, replace = _fill(search_t, caps), _fill(replace_t, caps)
        count = content.count(search)
        if count != 1:
            raise ValueError(f"Patch '{patch.name}': expected search string exactly once (found {count}): {search!r}")
        content = content.replace(search, replace, 1)
    return content


def apply_all(content: str, version: str) -> str:
    lines = content.split("\n", 1)
    header = PATCHED_HEADER.format(version=version)
    content = header + "\n" + (lines[1] if lines[0].startswith("//") else content)

    for patch in PATCHES:
        content = apply_patch(content, patch)

    return content


def verify(content: str) -> list[tuple[str, str, bool]]:
    return [
        ("Patch header", "StarHTML patched", "StarHTML patched" in content),
        *((f"Patch: {p.name}", m[:50], m in content) for p in PATCHES for m in p.markers),
    ]
