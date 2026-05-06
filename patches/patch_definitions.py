"""Patch definitions for vendored Datastar (search/replace + verification markers)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PatchDef:
    name: str
    operations: list[tuple[str, str]] = field(default_factory=list)  # (search, replace)
    markers: list[str] = field(default_factory=list)


PATCHED_HEADER = "// Datastar v{version} (StarHTML patched: shadow-dom-scan, outside-race-fix)"

PATCHES: list[PatchDef] = [
    PatchDef(
        name="shadow-dom-scan",
        operations=[
            (
                'En=(e=document.documentElement,t=!0)=>{Z(e)&&De([e],!0),De(e.querySelectorAll("*"),!0),',
                'En=(e=document.documentElement,t=!0,n=!0)=>{Z(e)&&De([e],n),De(e.querySelectorAll("*"),n),',
            ),
            (
                "export{I as action",
                'document.addEventListener("datastar:scan",e=>'
                "{let t=e.detail?.root;t&&En(t.shadowRoot||t,!0,!1)});"
                "export{I as action",
            ),
        ],
        markers=[
            "En=(e=document.documentElement,t=!0,n=!0)=>",
            '"datastar:scan",e=>{let t=e.detail',
        ],
    ),
    PatchDef(
        name="outside-race-fix",
        operations=[
            (
                'let o=O(t,n,"kebab"),a={capture:n.has("capture"),passive:n.has("passive"),once:n.has("once")};'
                'if(n.has("outside")){s=document;let l=i;i=u=>{e.contains(u?.target)||l(u)}}'
                "(o===B||o===te)&&(s=document);",
                'let o=O(t,n,"kebab"),a={capture:n.has("capture"),passive:n.has("passive"),once:n.has("once")},d;'
                'if(n.has("outside")){s=document;let l=i,u=!1,'
                "f=new MutationObserver(()=>{u=!0;"
                "requestAnimationFrame(()=>{u=!1})});"
                'f.observe(e,{attributeFilter:["style"]});'
                'let g=!1,h=()=>{g=e.style.display==="none"};'
                "document.addEventListener(o,h,!0);"
                "i=p=>{u||g||e.contains(p?.target)||l(p)};"
                "d=()=>{f.disconnect();"
                "document.removeEventListener(o,h,!0)}}"
                "(o===B||o===te)&&(s=document);",
            ),
            (
                "s.removeEventListener(o,c,a)}}});",
                "s.removeEventListener(o,c,a);d?.()}}});",
            ),
        ],
        markers=[
            "requestAnimationFrame(()=>{u=!1})",
            'e.style.display==="none"',
            'once:n.has("once")},d;if(n.has("outside")',
        ],
    ),
]


def apply_patch(content: str, patch: PatchDef) -> str:
    """Idempotent — skips if already applied."""
    if all(marker in content for marker in patch.markers):
        return content
    for search, replace in patch.operations:
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
