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
                "export{k as action",
                'document.addEventListener("datastar:scan",e=>'
                "{let r=e.detail?.root;r&&nn(r.shadowRoot||r,!0)});"
                "export{k as action",
            ),
        ],
        markers=['"datastar:scan",e=>{let r=e.detail'],
    ),
    PatchDef(
        name="outside-race-fix",
        operations=[
            (
                'a=L(t,n,"kebab");if',
                'a=L(t,n,"kebab"),b;if',
            ),
            (
                'if(n.has("outside")){s=document;let c=o;'
                "o=l=>{e.contains(l?.target)||c(l)}}",
                'if(n.has("outside")){s=document;let c=o,d=!1,'
                "f=new MutationObserver(()=>{d=!0;"
                "requestAnimationFrame(()=>{d=!1})});"
                'f.observe(e,{attributeFilter:["style"]});'
                "let h=!1,g=()=>{"
                'h=e.style.display==="none"};'
                "document.addEventListener(a,g,!0);"
                "o=l=>{d||h||(e.contains(l?.target)||c(l))};"
                "b=()=>{f.disconnect();"
                "document.removeEventListener(a,g,!0)}}",
            ),
            (
                "s.removeEventListener(a,o)}}});",
                "s.removeEventListener(a,o);b?.()}}});",
            ),
        ],
        markers=[
            "requestAnimationFrame(()=>{d=!1})",
            'e.style.display==="none"',
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
            raise ValueError(
                f"Patch '{patch.name}': expected search string exactly once "
                f"(found {count}): {search!r}"
            )
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
        *(
            (f"Patch: {p.name}", m[:50], m in content)
            for p in PATCHES
            for m in p.markers
        ),
    ]
