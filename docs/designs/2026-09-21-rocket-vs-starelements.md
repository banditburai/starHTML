# Datastar Rocket (1.0.4) vs StarElements

Date: 2026-09-21. Sources read: Datastar v1.0.4 `library/src/rocket/{runtime,template,codecs,for,conditional}.ts`
and `bundles/datastar-rocket.ts`; StarElements 0.1.1 wheel (`core.py`, `decorator.py`, `signals.py`,
`integration.py`, `static/starelements.js`) plus GitHub HEAD (0.1.3, `se-head.ts` notes); StarHTML's
`patches/patch_definitions.py` (shadow-dom-scan). Rocket has no docs in the repo; everything is from source.

## What Rocket is

A JS component runtime, not a templating add-on: `rocket(tag, {props, setup, render, onFirstRender, mode,
manifest})` registers a custom element (`runtime.ts:558-583`), queued until `datastar-ready`. Shadow DOM is the
**default** (`mode:'light'` opt-in). Props are codec-decoded plain values with attribute reflection; only `$$`
locals are signals, stored under a nested path `_rocket.<tag>.<id>` (`:857`). Rendering is a client tagged
template (`html\`\``) morphed into the mount root; light mode emulates `<slot>`. Refs (`data-rocket-ref`) are
collected by a MutationObserver; component actions dispatch through one global `@dispatchRocket` action that
walks composed ancestors to the owning host (`data-rocket-host`). `for.ts`/`conditional.ts` add
`data-for`/`data-if` client loops (unkeyed, truncating). Scanning inside the shadow root calls the engine's
`apply(shadowRoot, true)` directly (`:1531`), which the bundle does not export.

## Comparison

| Axis | Rocket | StarElements |
| --- | --- | --- |
| Definition | JS `rocket(tag, def)` | Python `@element` -> server-emitted `<template data-star:tag data-signal:x="int|=5">`; JS registers per template |
| Props -> signals | props are *not* signals; only `$$` locals are, nested path | every observed attribute is a signal, flat `${ns}_${camel}` name (`data-star-id` or counter) |
| Refs / actions | `data-rocket-ref` proxy; `@foo(` -> `@dispatchRocket("foo",` | `refs('name')` = querySelector; no component actions |
| Scoping rewrite | attribute-aware: `data-signals:x`, `data-bind:x`, `data-indicator`, `data-computed:x`, loop aliases, `__root` escape, string/regex-safe | regex `\$\$name` in attr values + `data-computed:`/`data-ref` rename; `data-bind:x` / `data-signals:x` keys not namespaced |
| Rendering | client template + morph; `adoptStyles` | server `<template>` cloned once; `data-star-id` hosts skip cloning (SSR hydration) |
| Shadow DOM | default open | light default, `shadow=True` opt-in |
| Scan inside component | engine `apply(shadowRoot)` (internal) | `datastar:scan` event -> StarHTML shadow-dom-scan patch |
| SSE into host | `data-scope-children` + upstream `datastar-scope-children` event rescopes raw `$$` in patched children | nothing: patched fragment with `$$` stays raw |
| Pre-upgrade guard | `data-rocket-deferred-ignore`: undefined hyphenated tags with `$$` attrs get `data-ignore` until upgrade | FOUC CSS only (`:not(:defined)`) |
| Manifests | `publishRocketManifests` POSTs `{tag, props, slots, events}` | `events` field exists, unused |
| Errors | named `createError` reasons; codec failures warn + default | `console.error` strings; parse failures can yield NaN |
| CSP | trusted-types `createHTML`; expressions via `compileExpression` (nonce script) | `new Function` + sloppy `with` for static/setup scripts: needs `unsafe-eval` |
| Size (raw / gzip) | rocket bundle 65,470 / 23,607 B vs datastar.js 33,553 / 13,382 B | starelements.min.js 5,135 B + datastar.js |

## Adopt into StarElements (ordered by value)

1. **`data-scope-children` support**: listen for upstream's `datastar-scope-children` (patchElements.ts:259-262,
   no patch needed) so SSE fragments patched into a host can carry `$$` and get namespaced before evaluation.
   Fixes a real gap in StarHTML's fragment-first model.
2. **Attribute-aware rewrite**: namespace `data-bind:x`, `data-signals:x`, `data-indicator`, `data-ref:x` *keys*,
   add a `__root` escape for page-scope signals (`template.ts:501-554`).
3. **Pre-upgrade `data-ignore` guard** for hosts whose attributes/light children carry `$$` until
   `connectedCallback` (`runtime.ts:343-397`). Same bug class as the same-element declaration-order issue.
4. **CSP path**: compile static/setup scripts through a nonced `<script>` when `<html data-nonce>` is present
   (mirror `engine/csp.ts:47-58`). StarHTML now ships `star_app(csp=True)`; StarElements is the remaining
   `unsafe-eval` consumer.
5. **Named errors + safe codec fallback** (warn and use default instead of NaN/throw).
6. **Manifest shape** `{tag, props, slots, events}` emitted server-side from `ElementDef`; wire `events`.
7. Optional: nested signal path `_star.<tag>.<id>.x` so one `mergePaths([[base,null]])` removes an instance.
   Breaks the flat-name contract StarHTML devtools match (`^_star_\w+_id\d+_`); only with a devtools update.

## Keep as is

- Server-rendered `<template>` + light DOM default (Rocket re-implements on the client what StarHTML renders on
  the server, and needs ~40 lines to emulate slots).
- Attributes-are-signals (simpler than props + `$$` split for a server-driven app).
- `data-star-id` hydration: Rocket has no SSR hydration at all.
- FOUC/skeleton CSS; 5 KB runtime.

## Not applicable

Codec DSL (Python validates at render time); `for.ts`/`conditional.ts` (unkeyed truncating client loops are a
regression for server-owned lists; StarHTML streams fragments); manifest POST; `@dispatchRocket` bridge (no
component-local JS actions in StarElements); `adoptStyles` (StarCSS covers light DOM).

## Risks / interaction with the shadow-dom-scan patch

- The patch cannot target `datastar-rocket.js` (two functions match the scan landmark; neither upstream bundle
  has a `datastar:scan` listener). Switching an app to the Rocket bundle silently loses StarElements scanning.
- Mixed page (patched core + Rocket loaded separately): Rocket's guard only fires on undefined hyphenated tags
  whose own attributes contain `$$`; StarElements rewrite `$$` before insertion, so no interference (inferred).
- Long-term: Rocket proves `apply(shadowRoot, true)` is the sanctioned primitive. An upstream export of `apply`
  (or an upstream `datastar:scan`) would turn patch 1 into a one-line listener that works on both bundles.
