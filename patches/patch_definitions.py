"""Patch definitions for vendored Datastar (search/replace + verification markers)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PatchDef:
    name: str
    operations: list[tuple[str, str]] = field(default_factory=list)  # (search, replace)
    markers: list[str] = field(default_factory=list)


PATCHED_HEADER = (
    "// Datastar v{version} (StarHTML patched: shadow-dom-scan,"
    " outside-race-fix, init-refire-fix, persist-aware-init)"
)

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
            # Hoist a,b declaration before outside block (avoids TDZ — the
            # new outside block references a and b, so they must be declared first)
            (
                'once:n.has("once")};if(n.has("outside"))',
                'once:n.has("once")};let a=L(t,n,"kebab"),b;if(n.has("outside"))',
            ),
            # Replace simple outside block with race-fix version
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
            # Remove original a declaration (now hoisted above)
            (
                'let a=L(t,n,"kebab");if',
                "if",
            ),
            # Add cleanup call
            (
                "s.removeEventListener(a,o)}}});",
                "s.removeEventListener(a,o);b?.()}}});",
            ),
        ],
        markers=[
            "requestAnimationFrame(()=>{d=!1})",
            'e.style.display==="none"',
            'once")};let a=L(t,n,"kebab"),b;if(n.has("outside")',
        ],
    ),
    PatchDef(
        name="init-refire-fix",
        operations=[
            # nn(): add 3rd param `f` (filter flag) and pass it to _e() calls.
            # When f is truthy, _e/xt only process newly-registered plugins (via Ze).
            # When f is undefined (shadow DOM scans), all plugins are processed.
            # This supersedes the earlier "scan-timing-fix" which bluntly removed
            # the hardcoded !0 — that broke plugin-registration rescans.
            (
                "nn=(e=document.documentElement,t=!0)=>"
                '{K(e)&&_e([e],!0),_e(e.querySelectorAll("*"),!0),',
                "nn=(e=document.documentElement,t=!0,f)=>"
                '{K(e)&&_e([e],f),_e(e.querySelectorAll("*"),f),',
            ),
            # p(): pass filter flag so plugin-registration rescans only process
            # the newly registered plugin, not re-fire data-init on every element.
            (
                "He.length=0,nn(),Ze.clear()",
                "He.length=0,nn(void 0,!0,!0),Ze.clear()",
            ),
        ],
        markers=[
            "nn=(e=document.documentElement,t=!0,f)=>",
            "nn(void 0,!0,!0)",
        ],
    ),
    PatchDef(
        name="signal-patch-source-tag",
        operations=[
            # Declare module-scoped _J_src at the very top of the code body.
            # J() includes it in the datastar-signal-patch event when non-empty,
            # allowing the debugger to get definitive source info (e.g. "persist").
            ("var at=", 'var _J_src="";var at='),
            # Patch J() to wrap detail in {signals, source} when _J_src is set.
            (
                "J=(e,t)=>{if(e!==void 0&&t!==void 0&&xe.push([e,t]),"
                "!Oe&&xe.length){let n=Me(xe);xe.length=0,"
                "document.dispatchEvent(new CustomEvent(Z,{detail:n}))}}",
                #
                "J=(e,t)=>{if(e!==void 0&&t!==void 0&&xe.push([e,t]),"
                "!Oe&&xe.length){let n=Me(xe);xe.length=0;"
                "let _d=_J_src?{signals:n,source:_J_src}:n;"
                "document.dispatchEvent(new CustomEvent(Z,{detail:_d}))}}",
            ),
        ],
        markers=['var _J_src=""', "signals:n,source:_J_src"],
    ),
    PatchDef(
        name="persist-aware-init",
        operations=[
            # Patch mergePatch (O) so that ifMissing mode checks localStorage/
            # sessionStorage for starhtml-persist* keys before setting defaults.
            # Signals start with the persisted value on the very first render —
            # zero FOUC.  Sets _J_src="persist" so the signal-patch event carries
            # definitive source metadata for the debugger.
            (
                "O=(e,{ifMissing:t}={})=>{M();"
                'for(let n in e)e[n]==null?t||delete X[n]:vt(e[n],n,X,"",t);x()}',
                #
                "O=(e,{ifMissing:t}={})=>{"
                "if(t){let _ps=window.__starhtml_pc;"
                "if(_ps===void 0){_ps={};"
                "try{for(let _st of[localStorage,sessionStorage])"
                "{for(let _i=0;_i<_st.length;_i++){let _k=_st.key(_i);"
                'if(_k?.startsWith("starhtml-persist"))'
                "{try{let _d=JSON.parse(_st.getItem(_k));"
                'if(_d&&typeof _d==="object")Object.assign(_ps,_d)}'
                "catch{}}}}}catch{}"
                "window.__starhtml_pc=_ps}"
                "let _hp=!1;"
                "for(let n in e)if(n in _ps&&_ps[n]!=null){e[n]=_ps[n];_hp=!0}"
                'if(_hp)_J_src="persist"}'
                "M();"
                'for(let n in e)e[n]==null?t||delete X[n]:vt(e[n],n,X,"",t);x();'
                '_J_src=""}',
            ),
        ],
        markers=["window.__starhtml_pc", '_J_src="persist"'],
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
