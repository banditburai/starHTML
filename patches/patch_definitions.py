"""Patch definitions for vendored Datastar.

Datastar's minified bundle reassigns single-char identifiers every release, so
patches anchored on those names break on each upgrade. Instead each patch captures
its volatile tokens from stable string/structural landmarks, then fills `«token»`
placeholders in the search/replace operations. Guillemets are used (not f-strings
or .format) because the JS payloads are full of unescaped `{}`.
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
    reserved: frozenset[str] = frozenset()  # identifiers the replacement introduces; captures must not reuse them


PATCHED_HEADER = "// Datastar v{version} (StarHTML patched: shadow-dom-scan, outside-race-fix)"

PATCHES: list[PatchDef] = [
    PatchDef(
        name="shadow-dom-scan",
        captures={
            "fn": r"(\w+)=\(e=\w+\.documentElement,t=!0\)=>\{",  # scan function
            "doc": r"=\(e=(\w+)\.documentElement,t=!0\)=>\{",  # `document` or its minified alias (1.0.4+)
            "chk": r"=\(e=\w+\.documentElement,t=!0\)=>\{(\w+)\(e\)&&",  # connected-check
            "scan": r"=>\{\w+\(e\)&&(\w+)\(\[e\],!0\),",  # attribute-scan helper
            "act": r"export\{(\w+) as action",  # `action` export alias
            "roots": r"=\(\)=>(\w+)\.has\(\w+\.documentElement\)",  # observed-roots Set (drives the deferred first scan)
            "ready": r'(\w+)="datastar-ready"',  # DATASTAR_READY_EVENT const
        },
        operations=[
            # Add a third filter arg `n` (default keep upstream behavior) threaded to both
            # scan calls, so explicit shadow-root scans can bind all loaded plugins.
            (
                '«fn»=(e=«doc».documentElement,t=!0)=>{«chk»(e)&&«scan»([e],!0),«scan»(e.querySelectorAll("*"),!0),',
                '«fn»=(e=«doc».documentElement,t=!0,n=!0)=>{«chk»(e)&&«scan»([e],n),«scan»(e.querySelectorAll("*"),n),',
            ),
            # StarElements' `datastar:scan` event has no upstream listener; add one that
            # scans the provided (shadow) root with no plugin filter. `document` is spelled
            # literally here on purpose: this runs at module scope, outside any alias.
            #
            # Datastar defers its first scan to a timeout and then scans `roots.size ? [...roots]
            # : [documentElement]`. A host that connects before that timeout (StarElements
            # defines its elements as soon as its module runs) must not register itself as a
            # root, or the document is never scanned: light-DOM hosts are covered by the pending
            # document scan, shadow roots are scanned once `datastar-ready` fires.
            (
                "export{«act» as action",
                'document.addEventListener("datastar:scan",e=>{let t=e.detail?.root;if(!t)return;'
                "let r=t.shadowRoot||t,s=()=>«fn»(r,!0,!1);"
                "«roots».has(document.documentElement)?s():r instanceof ShadowRoot&&document.addEventListener(«ready»,s,{once:!0})});"
                "export{«act» as action",
            ),
        ],
        markers=[
            'e.querySelectorAll("*"),n),',
            'document.addEventListener("datastar:scan",e=>{let t=e.detail?.root;if(!t)return;',
        ],
    ),
    PatchDef(
        name="outside-race-fix",
        captures={
            "kebab": r'let o=(\w+)\(t,n,"kebab"\)',  # event-name kebab helper
            "doc": r'if\(n\.has\("outside"\)\)\{s=(\w+);let \w+=i;',  # `document` or its minified alias (1.0.4+)
            "saved": r'if\(n\.has\("outside"\)\)\{s=\w+;let (\w+)=i;',  # saved inner handler
            "arg": r"i=(\w+)=>\{e\.contains\(\1\?\.target\)\|\|",  # outside-handler event param
            "ev": r"\}\((o===\w+\|\|o===\w+)\)&&\(s=\w+\);",  # focus/blur event consts
            "listener": r"s\.removeEventListener\(o,(\w+),a\)\}\}\}\);",  # registered listener
        },
        operations=[
            # Suppress spurious `outside` events during the gesture that opened the element:
            # a MutationObserver+rAF flag (cross-event) and a capture-phase display:none
            # snapshot (same-event). `d` tears both down on listener removal.
            (
                'let o=«kebab»(t,n,"kebab"),a={capture:n.has("capture"),passive:n.has("passive"),once:n.has("once")};'
                'if(n.has("outside")){s=«doc»;let «saved»=i;i=«arg»=>{e.contains(«arg»?.target)||«saved»(«arg»)}}'
                "(«ev»)&&(s=«doc»);",
                # Introduced locals use a `_` prefix so they cannot collide with minified captures.
                'let o=«kebab»(t,n,"kebab"),a={capture:n.has("capture"),passive:n.has("passive"),once:n.has("once")},_d;'
                'if(n.has("outside")){s=«doc»;let «saved»=i,_u=!1,'
                "_f=new MutationObserver(()=>{_u=!0;requestAnimationFrame(()=>{_u=!1})});"
                '_f.observe(e,{attributeFilter:["style"]});'
                'let _g=!1,_h=()=>{_g=e.style.display==="none"};'
                "«doc».addEventListener(o,_h,!0);"
                "i=_e=>{_u||_g||e.contains(_e?.target)||«saved»(_e)};"
                "_d=()=>{_f.disconnect();«doc».removeEventListener(o,_h,!0)}}"
                "(«ev»)&&(s=«doc»);",
            ),
            (
                "s.removeEventListener(o,«listener»,a)}}});",
                "s.removeEventListener(o,«listener»,a);_d?.()}}});",
            ),
        ],
        markers=[
            "requestAnimationFrame(()=>{_u=!1})",
            'e.style.display==="none"',
            'once:n.has("once")},_d;if(n.has("outside")',
        ],
        reserved=frozenset({"_d", "_u", "_f", "_g", "_h", "_e"}),
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
    clashes = {k: v for k, v in caps.items() if v in patch.reserved}
    if clashes:
        raise ValueError(f"Patch '{patch.name}': captured names collide with introduced locals: {clashes}")
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
    for search, replace in patch.operations:
        search, replace = _fill(search, caps), _fill(replace, caps)
        if (count := content.count(search)) != 1:
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
