# Datastar 1.0.1 Migration Matrix

StarHTML currently vendors upstream Datastar `1.0.0-RC.7` in
`patches/datastar-upstream.js` and applies StarHTML-specific runtime patches
from `patches/patch_definitions.py`.

This document tracks the migration from `1.0.0-RC.7` to `1.0.1`, the stable
version we intend to vendor. Intermediate releases are useful for understanding
behavioral changes, but implementation should target `1.0.1` directly.

## Migration Principles

- Vendor only the final target version, `1.0.1`, unless a blocker is found.
- Use `RC8` and `1.0.0` only to understand why behavior changed.
- Retarget StarHTML runtime patches against the `1.0.1` minified bundle once.
- Separate upstream compatibility tests from StarHTML-specific patch tests.
- Keep optional feature work, such as native `@intl` or `data-match-media`
  plugins, out of the core migration unless explicitly scoped.
- Do not copy Datastar Pro plugin source. If StarHTML adds native equivalents,
  implement from documented behavior and browser APIs only.

## Current StarHTML Runtime Patches

| Patch | Purpose | 1.0.1 status | Migration decision |
| --- | --- | --- | --- |
| `shadow-dom-scan` | Lets StarHTML components dispatch `datastar:scan` so Datastar scans shadow roots. | Existing minified anchor does not apply to `1.0.1`. | Keep behavior, retarget using the new `apply`/`applyElement` exports if possible. |
| `outside-race-fix` | Prevents `data-on:*__outside` from closing a newly opened `data-show` popover during the same user gesture. | Existing anchors partially match but the replacement does not apply. Upstream `data-on` changed in `1.0.0`. | Keep behavior, rewrite against `1.0.1` `data-on` structure and preserve upstream `__document`, cleanup options, prevent/stop ordering. |
| `init-refire-fix` | Prevents late plugin registration from re-firing `data-init`. | Likely obsolete. Upstream introduced queued-plugin scans in `RC8` and expanded observed-root scanning in `1.0.0`. | Remove if browser tests prove late plugin registration no longer re-fires `data-init` with StarHTML plugin loading. |
| `starhtml-signal-source-event` | Adds StarHTML-owned source metadata, especially for devtools persist attribution. | Implemented as a separate `starhtml:signal-source` event so the Datastar patch event remains vanilla. | Keep source metadata out of `datastar-signal-patch`; correlate in devtools. |
| `persist-aware-init` | Lets `data-signals__ifmissing` use persisted StarHTML values before defaults are rendered. | Existing anchor does not apply. Upstream still does not know StarHTML's custom persist storage. | Keep unless the StarHTML persist plugin is redesigned. Retarget carefully around `mergePatch`. |

## Release Matrix: RC7 to RC8

| Change | Upstream behavior | StarHTML impact | Risk | Required action | Verification |
| --- | --- | --- | --- | --- | --- |
| Added Pro `data-match-media` | Sets a signal from `window.matchMedia(query).matches` and keeps it updated on query changes. | New optional feature only. Not in free Datastar bundle. | Low for migration, medium if implemented. | No migration action. Consider a native StarHTML plugin later, implemented from docs/browser APIs only. | Separate plugin tests if added: initial match, change event, casing modifiers, cleanup. |
| Added Pro `@intl` | Formats values via browser `Intl` APIs. | New optional feature only. Not in free Datastar bundle. | Low for migration. | No migration action. Consider a native StarHTML action plugin later. | Separate action tests if added: number, datetime, pluralRules, relativeTime, list, displayNames, locale/options. |
| `requestCancellation: "auto"` no longer aborts on attribute cleanup | `auto` aborts the previous request from the same element but does not abort merely because the initiating element/attribute is removed. New `"cleanup"` opts into cleanup aborting. | StarHTML `post/get/...` helpers pass options through. User code may rely on old cleanup cancellation semantics. | Medium. | Update docs/tests. Consider documenting or supporting Python helper arg `request_cancellation="cleanup"` if snake-case conversion exists. | Browser test: remove initiating element during request under `auto` vs `cleanup`. |
| Retry uses current signals | Backend action retry rebuilds payload from current signals instead of initial payload snapshot. | Better correctness for live state. StarHTML should inherit after vendoring. | Medium. | No Python code action unless helper docs mention old behavior. | Browser/integration test: mutate signal before retry; server receives latest signal. |
| `$` inside string/template literals no longer parsed as signal refs | Expressions like `'$foo'` stay literal. Template interpolation has limited signal rewrite support. | May fix StarHTML-generated strings containing `$` or selectors. Could affect code that accidentally relied on old parsing. | Medium. | Add expression parsing regression tests around literals and template strings. | Browser test or direct runtime test: `data-text="'$foo'"`, template with `${$foo}`. |
| `datastar-patch-elements` accepts `Element` and `DocumentFragment` payloads | Watcher can consume/move DOM nodes directly, not only parse strings. Non-string payloads are single-use and target first match. | Mostly internal JS API. StarHTML SSE sends strings, but custom plugins/actions could use direct payloads. | Low. | No Python action. Add runtime compatibility test if we use this path later. | Browser test: dispatch event with Element/DocumentFragment payload. |
| `data-attr` preserves function values | Function values are stringified instead of becoming `{}` or being lost in JSON serialization. | Helpful for attributes like inline callbacks or serialized custom props. | Low. | No StarHTML code action. | Browser test: `data-attr="{foo: () => 1}"` sets function string. |
| `data-on` cleanup fixes `__capture` | Listener removal uses the same options object, so capture listeners are removed. | Good upstream fix. StarHTML `outside-race-fix` must preserve it. | High because our patch touches `data-on`. | Ensure retargeted `outside-race-fix` removes listener with options and its own extra cleanup. | Browser test: remove element with `data-on:click__capture`; listener no longer fires. |
| `data-on-intersect__threshold.N` fixed | Threshold modifier reads the first modifier tag instead of coercing the `Set`. | StarHTML already emits modifier tags for `threshold`. | Low. | No Python action. | Browser/unit test if feasible: `__threshold.25` maps to `0.25`. |
| Engine scanning reworked for queued attributes | Upstream splits normal scans from queued-plugin registration scans. Queued scans process only newly registered plugins. | Overlaps with StarHTML `init-refire-fix`. | High. | Reevaluate/remove `init-refire-fix`. Ensure StarHTML plugin loading does not re-run `data-init`. | Browser test: page with `data-init`, then load StarHTML plugin module; `data-init` fires once. |
| Attribute alias handling refined | `unaliasify` centralizes alias checks and raw `data-*` attributes are considered beyond `dataset`. | Mostly upstream internals. | Low. | No action unless StarHTML aliases Datastar attributes. | Existing attribute tests plus browser smoke. |

## Release Matrix: RC8 to 1.0.0

| Change | Upstream behavior | StarHTML impact | Risk | Required action | Verification |
| --- | --- | --- | --- | --- | --- |
| Payload resent after visibility reconnect | Fetch action rebuilds request init when a hidden tab becomes visible again. | Inherits by vendoring. Important for long-lived fetch/SSE with changed signals. | Medium. | No Python action. | Browser test: start request, change signal, simulate visibility reconnect, assert latest payload. |
| JSON `Content-Type` only when a body exists | `Content-Type: application/json` is not set for methods that send payload in query params. | Changes server-observed headers for `GET`/`DELETE`. StarHTML handlers should not assume JSON content type on GET. | Medium. | Check tests expecting JSON `Content-Type` on GET/DELETE. Update docs if needed. | Integration test: `@get` sends `datastar` query and no JSON content type. |
| Body only sent for non-GET and non-DELETE | `GET` and `DELETE` encode Datastar payload in query string; no request body. | Aligns with HTTP expectations. StarHTML request parsing should support query payload. | Medium. | Verify StarHTML server helpers read signals from query for GET/DELETE and body for POST/PUT/PATCH. | Integration tests for all fetch verbs. |
| `data-bind__prop` added | Binding can use a specific element property. In `1.0.0`, `__prop` required `__event`. | StarHTML kwarg processing must emit valid bare signal names with modifiers. | High. | Update `process_datastar_kwargs` tuple handling for `_SIGNAL_PATH_ATTRS` when expression is a Signal. Add tests. | Unit test: `data_bind=(Signal("open"), {"prop": "checked"})` renders `data-bind__prop.checked="open"` or keyed equivalent as intended. |
| `data-bind__event` added | Binding can sync from specific events. In `1.0.0`, `__event` required `__prop`; fixed in `1.0.1`. | Same Python modifier emission path as `__prop`. | High. | Target `1.0.1` semantics; allow `event` alone and `prop` alone. | Unit/browser tests for event-only, prop-only, prop+event. |
| `data-bind` respects initial checked radio | Missing radio signal adopts initially checked radio button. | Good upstream fix; may change initial signal values in forms. | Medium. | No Python action. Ensure StarHTML form demos still behave. | Browser test: radio group with checked item and undefined signal initializes to checked value. |
| `data-on__document` added | Event listener can attach to `document`. | StarHTML `_build_modifier_suffix` can already emit `document` modifier. `outside-race-fix` must preserve target selection order. | Medium. | Add test for `data_on_x=(..., {"document": True})`; ensure no collision with Datastar fetch/signal events. | Browser test: document event triggers handler. |
| Morphing of `input`, `select`, `textarea` improved | Morph updates value/checked/selected/disabled/default value more carefully. Emits `datastar-prop-change` when properties change. | Important for StarHTML SSE patching and forms. May alter previous behavior. | High. | Add browser regression tests for patched forms. Audit demos using form updates. | Browser tests: text input, checkbox, radio, select, textarea preserve/update expected state after patch. |
| New `datastar-prop-change` event | `data-bind` listens for this event after morph-driven property updates instead of native `change`. | Inherits by vendoring. StarHTML plugins should avoid faking native `change` when morphing. | Medium. | No Python action. Add tests if we patch/morph bound form controls. | Browser test: patch input value; bound signal updates via prop-change. |
| `kebab` handles consecutive uppercase letters | Names like `URLValue` become better kebab-case. | Could affect attribute/event casing if StarHTML passes camel/Pascal names to Datastar. | Low. | No action unless tests assume old casing. | Unit/browser casing tests for event and class names if relevant. |
| Submit input value included in form submissions | `<input type="submit" name=...>` submitter value is included, not just button submitters. | StarHTML forms may benefit. | Low. | No action. | Integration test with submit input name/value. |
| `__viewtransition` no longer interferes with modifiers/methods | Event-side effects (`prevent`, `stop`, submit prevention) are applied before timing/view-transition wrappers. | Our `outside-race-fix` must preserve this new listener wrapper order. | High. | Retarget `outside-race-fix` around final `listener`, not old `callback`. | Browser test: `data-on:submit__viewtransition__prevent` prevents submit. |
| `retryMaxWaitMs` renamed to `retryMaxWait` | Fetch option name changed. | StarHTML action helper passes kwargs literally. Existing user code may pass old camel name. | Medium. | Prefer documenting new name. Consider accepting Pythonic `retry_max_wait` in helper if option normalization is introduced. Avoid silently emitting stale `retryMaxWaitMs`. | Unit test action helper emits `retryMaxWait`. |
| Engine exports and lifecycle changed | Adds `datastar-ready`, tracks observed roots as a `Set`, exports `applyElement` and `genRx`. Late plugin registration scans observed roots. | Could simplify `shadow-dom-scan` patch and reduce need for `init-refire-fix`. | High. | Use new exports/structure when retargeting. Test StarHTML shadow DOM and plugin registration behavior. | Browser tests for shadow-root scan and late plugin load. |
| Indicator tracks overlapping fetches | Indicator signal stays true until all fetches from the element finish. | More correct for concurrent actions. | Low/medium. | No Python action. | Browser test with two overlapping requests. |
| Template morphing improved | `HTMLTemplateElement` innerHTML is handled specially. | May help StarHTML component/template patterns. | Low. | No action. | Covered by broad patch-elements smoke tests. |
| `moveBefore` wrapper changed | Uses native `moveBefore` if available, otherwise `insertBefore`. | Internal morphing detail. | Low. | No action. | Covered by morphing tests. |
| Rocket rewritten as JS API | Docs/API changed. | No observed StarHTML dependency. | Low. | No action unless StarHTML later integrates Rocket. | None. |

## Release Matrix: 1.0.0 to 1.0.1

| Change | Upstream behavior | StarHTML impact | Risk | Required action | Verification |
| --- | --- | --- | --- | --- | --- |
| `data-bind__prop` and `__event` independent | `__prop` can override only the property while keeping default events; `__event` can override only events while keeping default property/adapter. | StarHTML tuple modifier emission must support either modifier alone. | High. | Add unit tests for prop-only, event-only, and prop+event. Fix `process_datastar_kwargs` for Signal values with modifiers. | Unit and browser tests. |
| `__prop` value camel-cased | `__prop.selected-index` binds through `selectedIndex`. | StarHTML modifier syntax should allow hyphenated prop tags. `_build_modifier_suffix` currently uses raw string value, so this should work. | Medium. | Document/test expected output. No runtime code if output is `__prop.selected-index`. | Unit test output and browser custom element/property test. |
| Single `select` with no initial signal stays string | Select initial signal no longer coerces to number when undefined. | May affect form assumptions. Usually correct. | Medium. | Add browser test for select with value `"1"` and no predefined signal; signal should be string `"1"`. | Browser test. |

## StarHTML Code Audit Checklist

| Area | Files | Questions | Action |
| --- | --- | --- | --- |
| Vendored source/version | `patches/datastar-upstream.js`, `src/starhtml/starapp.py` | Is upstream source exactly `1.0.1`? Does `DATASTAR_VERSION` include `1.0.1+starhtml`? | Update via `scripts/update_datastar.py 1.0.1` after patches are ready or use it to fetch and then retarget patches. |
| Runtime patch definitions | `patches/patch_definitions.py` | Which patches remain necessary? Which anchors apply? Are markers robust enough? | Retarget to `1.0.1`; remove obsolete `init-refire-fix` if tests pass without it. |
| Patch verification | `patches/verify_datastar_patches.py` | Do markers prove all StarHTML runtime behavior is present? | Update markers for final patched bundle. |
| Datastar kwarg normalization | `src/starhtml/datastar.py` | Do Signal values in tuple/modifier form render as bare signal paths for `data_bind`, `data_ref`, `data_indicator`? | Fix tuple branch for `_SIGNAL_PATH_ATTRS`. |
| Fetch helper options | `src/starhtml/datastar.py` | Are options emitted with current Datastar names, especially `retryMaxWait`? | Add or document normalization strategy. |
| Plugin loader timing | `src/starhtml/plugins.py`, TypeScript plugins | Does loading plugins after initial Datastar scan re-run `data-init`? | Browser test and patch decision. |
| Persist prehydration | `typescript/plugins/persist.ts`, `patches/patch_definitions.py` | Does StarHTML persist still avoid default-value flash with `data-signals__ifmissing`? | Retarget `persist-aware-init`; browser test local/session storage. |
| Devtools source metadata | `src/starhtml/devtools.py`, `typescript/devtools/*`, `patches/patch_definitions.py` | Does devtools still expect `{signals, source}` for signal patches? | Devtools listens for `starhtml:signal-source` and correlates with vanilla Datastar patch events. |
| Shadow DOM components | StarHTML custom elements/components | Does `datastar:scan` still bind attributes inside shadow roots? | Retarget `shadow-dom-scan`; browser test. |
| Popover/outside behavior | demos/components using `data-show` + `__outside` | Does opening a popover close it during the same click/mouse gesture? | Retarget `outside-race-fix`; browser test click and mouseup/click variants. |

## Proposed Test Plan

### Unit Tests

- `process_datastar_kwargs` renders `data_bind=(Signal("x"), {"prop": "checked"})`
  with a bare signal path, not `$x`.
- `process_datastar_kwargs` renders `data_bind=(Signal("x"), {"event": "change"})`
  with a bare signal path.
- `process_datastar_kwargs` renders `data_bind=(Signal("x"), {"prop": "selected-index", "event": "change"})`
  and preserves the hyphenated modifier tag.
- Fetch action helper can emit `retryMaxWait` and does not encourage
  `retryMaxWaitMs`.
- `data_on_*` modifiers can emit `__document`.
- Existing modifier rendering for `__capture`, `__viewtransition`,
  `__prevent`, and `__outside` remains stable.

### Browser Tests

- Datastar runtime boots and dispatches/observes normal bindings under `1.0.1`.
- `data-init` fires once when StarHTML plugins load after the page scan.
- `datastar:scan` binds inside shadow roots.
- `data-on:click__outside` does not close a just-opened `data-show` element in
  same-event and cross-event cases.
- `data-on:click__capture` cleanup removes the capture listener.
- `data-on:custom__document` receives document events.
- `data-on-intersect__threshold.25` uses threshold `0.25`.
- Expression parser leaves literal `'$foo'` unchanged.
- Template literal interpolation with `${$foo}` still reads signal value.
- `data-bind__prop`, `data-bind__event`, and combined `__prop`/`__event` work.
- Radio group adopts initially checked value when signal is missing.
- Single select missing signal initializes as string, not number.
- Morphing bound inputs/textareas/selects updates signals through
  `datastar-prop-change`.
- Indicator stays true for overlapping fetches until all complete.
- GET and DELETE actions send signals in query string and no request body.
- POST/PUT/PATCH actions send JSON body and correct content type.
- Retry/visibility reconnect rebuilds payload from current signals.
- `requestCancellation: "auto"` and `"cleanup"` differ as expected.
- StarHTML persist prehydrates values before `data-signals__ifmissing` defaults.

### Integration/Smoke Tests

- Run existing unit test suite.
- Run existing browser compatibility tests.
- Run key web demos that exercise:
  - forms and validation,
  - live updates/SSE,
  - plugins loaded through `plugins_hdrs`,
  - popovers/menus using `__outside`,
  - persisted state,
  - component/shadow DOM scans if present.

## Implementation Sequence

1. Add migration tests that can run against the current runtime where possible.
   Mark tests that require `1.0.1` behavior if needed.
2. Download/vendor upstream `1.0.1`.
3. Retarget `patches/patch_definitions.py` against the `1.0.1` bundle.
4. Decide whether to remove `init-refire-fix` based on browser tests.
5. Update StarHTML Python helpers for `data_bind` modifiers and fetch option
   naming.
6. Run patch verification.
7. Run unit tests.
8. Run browser tests and demo smoke tests.
9. Update any public docs or examples that mention old Datastar option names or
   old behavior.

## Beads Tracking Plan

The implementation work is tracked under epic `starhtml-upstream-5bg`
(`Datastar 1.0.1 Runtime Migration`).

The detailed local execution plan is registered in beads config as:
`docs/plans/2026-05-06-datastar-1-0-1-runtime-migration.md`.

Note: this repository currently ignores `docs/` and `.beads/`, so this section
mirrors the bead graph in a tracked file.

| Task ID | Review ID | Work |
| --- | --- | --- |
| `starhtml-upstream-5bg.3` | `starhtml-upstream-5bg.16` | Task 1: Add Datastar runtime browser test harness |
| `starhtml-upstream-5bg.4` | `starhtml-upstream-5bg.17` | Task 2: Add unit tests for StarHTML Datastar kwarg alignment |
| `starhtml-upstream-5bg.5` | `starhtml-upstream-5bg.18` | Task 3: Add fetch action migration tests |
| `starhtml-upstream-5bg.6` | `starhtml-upstream-5bg.19` | Task 4: Add `data-on` migration tests |
| `starhtml-upstream-5bg.7` | `starhtml-upstream-5bg.20` | Task 5: Add `data-bind` and form initialization tests |
| `starhtml-upstream-5bg.8` | `starhtml-upstream-5bg.21` | Task 6: Add morphing and `datastar-prop-change` tests |
| `starhtml-upstream-5bg.9` | `starhtml-upstream-5bg.22` | Task 7: Add StarHTML runtime patch behavior tests |
| `starhtml-upstream-5bg.10` | `starhtml-upstream-5bg.23` | Task 8: Vendor upstream Datastar `1.0.1` |
| `starhtml-upstream-5bg.11` | `starhtml-upstream-5bg.24` | Task 9: Retarget runtime patches against `1.0.1` |
| `starhtml-upstream-5bg.12` | `starhtml-upstream-5bg.25` | Task 10: Update StarHTML Python API alignment |
| `starhtml-upstream-5bg.13` | `starhtml-upstream-5bg.26` | Task 11: Make migration tests pass on patched `1.0.1` |
| `starhtml-upstream-5bg.14` | `starhtml-upstream-5bg.27` | Task 12: Run demo smoke checks and update docs |
| `starhtml-upstream-5bg.15` | `starhtml-upstream-5bg.28` | Task 13: Final quality gate and handoff |

Initial ready work:

- `starhtml-upstream-5bg.3`: Task 1, browser harness.
- `starhtml-upstream-5bg.4`: Task 2, Python kwarg alignment unit tests.

Review workflow:

- Each review bead is P1 and blocked by its implementation bead.
- When an implementation bead closes, its review bead becomes ready and should
  be completed before starting additional P2 implementation work.

## Open Decisions

- Should StarHTML support a backwards-compatible `retryMaxWaitMs` alias, or
  should we require the upstream `retryMaxWait` spelling after the migration?
- Should Python kwargs normalize snake_case Datastar action options
  (`retry_max_wait`) to camelCase (`retryMaxWait`), or continue passing kwargs
  literally?
- Should native StarHTML equivalents for `@intl` and `data-match-media` use the
  exact Datastar Pro names or StarHTML-specific names?
- Can `shadow-dom-scan` be implemented via a cleaner exported API in `1.0.1`
  instead of calling an internal minified scan function?
- Can `persist-aware-init` move out of the minified runtime patch and into the
  StarHTML persist plugin/bootstrap path?

## Native Pro-Equivalent Evaluation Notes

These evaluations are implementation guidance only. Do not copy Datastar Pro
source; implement from the public behavior and browser APIs.

### Native `@intl` action

- Recommendation: implement a native StarHTML action plugin using the public
  `@intl(type, value, options?, locale?)` surface so Datastar examples can be
  ported with minimal friction.
- Scope: support `number`, `datetime`, `pluralRules`, `relativeTime`, `list`,
  and `displayNames` using the corresponding browser `Intl.*` constructors.
- API notes: `relativeTime` needs either a value/unit convention or an options
  field for the unit; `displayNames` requires `options.type`; invalid types or
  constructor errors should warn and return a stable fallback string rather than
  throwing during reactive expression evaluation.
- StarHTML integration: add `typescript/plugins/intl.ts`, register it as a
  `Plugin("intl", file_actions=True, actions=("",))`, export it from
  `src/starhtml/plugins.py`, and add docs/API examples. Because action plugins
  are used inside expressions, verify the Datastar action hook returns computed
  values as expected.
- Tests: browser coverage for locale/options handling and every supported type,
  plus Python helper/import-map tests that `plugins_hdrs(intl)` registers the
  action plugin.

### Native `data-match-media` attribute

- Recommendation: implement a native StarHTML attribute plugin matching the
  public `data-match-media:<signal>="<query>"` behavior.
- Scope: normalize simple query values such as `prefers-color-scheme: dark` to
  `(prefers-color-scheme: dark)`, preserve explicitly parenthesized complex
  queries, set the signal immediately from `window.matchMedia(query).matches`,
  listen for `change`, and remove the listener on cleanup.
- Casing: support Datastar-style `__case.camel|kebab|snake|pascal` modifiers for
  the signal key. Reuse local casing helpers if available; otherwise keep the
  implementation local and covered by tests.
- StarHTML integration: add `typescript/plugins/match-media.ts`, expose
  `match_media = Plugin("match-media")` from `src/starhtml/plugins.py`, and add
  docs/demo coverage for color scheme and reduced-motion queries.
- Tests: browser tests for initial match, change event updates with mocked
  `matchMedia`, query normalization, casing modifiers, and cleanup after the
  attribute/element is removed.

## Source References

- Datastar `v1.0.0-RC.8` release notes:
  <https://github.com/starfederation/datastar/releases/tag/v1.0.0-RC.8>
- Datastar `v1.0.0` release notes:
  <https://github.com/starfederation/datastar/releases/tag/v1.0.0>
- Datastar `v1.0.1` release notes:
  <https://github.com/starfederation/datastar/releases/tag/v1.0.1>
- Datastar attributes reference:
  <https://data-star.dev/reference/attributes>
- Datastar actions reference:
  <https://data-star.dev/reference/actions>
