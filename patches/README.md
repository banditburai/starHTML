# Datastar Vendored Patches

Vanilla source: `patches/datastar-upstream.js` (committed)
Patched output: `src/starhtml/static/js/datastar.js` (gitignored, built by `bun run build`)
Version tracked in `DATASTAR_VERSION` (`starapp.py`), with `+starhtml` build metadata suffix.

## Build Pipeline

`bun run build` calls `scripts/build_datastar.py` which:
1. Reads `patches/datastar-upstream.js`
2. Applies all patches from `patches/patch_definitions.py`
3. Verifies all patch markers
4. Writes to `src/starhtml/static/js/datastar.js`

The patched file is served alongside plugins and debugger JS via the general `/_pkg/starhtml/{filename}` route.

## Updating Datastar

```
python scripts/update_datastar.py 1.0.1
bun run build
```

(The `v` prefix is optional — `v1.0.1` also works.)

This downloads vanilla Datastar from CDN, dry-runs all patches to verify they apply, saves the vanilla source to `patches/datastar-upstream.js`, and updates `DATASTAR_VERSION`.

If a patch fails (Datastar internals changed), the script saves `patches/datastar-upstream.vanilla.js` for diffing. Fix the search strings in `patches/patch_definitions.py`.

To verify patches on the current built file:

```
python patches/verify_datastar_patches.py
```

## Opting Out

```python
app, rt = star_app(datastar="cdn")
```

Serves vanilla Datastar from CDN. Shadow DOM components (StarElements) require the scan patch and will not work.

## Patch 1: Shadow DOM Scan Listener

**Problem**: Datastar's `MutationObserver` cannot see inside shadow trees. The `datastar:scan` custom event dispatched by StarElements has no listener, so shadow DOM components get zero reactive bindings.

**Fix**: Added a `document.addEventListener("datastar:scan", ...)` that calls Datastar's internal `En` (scan) function on the provided root. The scan function now accepts a third filter argument: normal late-plugin rescans keep upstream's newly-registered-plugin filter, while explicit `datastar:scan` calls pass no filter so all loaded plugins bind inside the shadow root.

**Note**: The minified function name `En` may change across versions. Look for the function that calls the attribute scan helper on descendants and sets up a `MutationObserver`.

## Patch 2: Outside Modifier Race Fix

**Problem**: When a user gesture opens a popover (via `data-show`) and an `outside` handler fires in the same interaction, the popover opens and closes instantly. Two variants:

1. **Cross-event**: `mouseup` opens popover → `click` fires (same gesture, separate event) → outside handler closes it
2. **Same-event**: `click` opens popover → same `click` propagates to document → outside handler closes it

**Fix**: Two complementary mechanisms:

- **MutationObserver + rAF** (cross-event): Watches the element's `style` attribute. On mutation, sets a flag cleared by `requestAnimationFrame`. Outside events arriving while the flag is set are suppressed.
- **Capture-phase snapshot** (same-event): Registers a capture-phase listener for the same event type. At capture phase, snapshots whether the element is hidden (`display: none`). If it was hidden when the event started, the outside handler suppresses.

**Scope**: The `e.style.display === "none"` check only detects inline styles set by `data-show`. This is an intentional coupling — `data-show` is the primary use case for `outside` modifiers.

## Obsolete: Init Refire Fix

Older StarHTML builds patched Datastar's scan function to prevent `data-init` from firing twice when plugins registered after the first page scan.

Datastar `1.0.1` tracks observed roots and preserves the newly-registered-plugin filter during late plugin registration. StarHTML now relies on that upstream behavior, backed by the browser migration test for late plugin registration. The shadow DOM scan patch still adds a filter override for explicit component scans, but there is no longer a separate `init-refire-fix` patch.

## Patch 3: StarHTML Signal Source Event

**Problem**: The debugger needs to distinguish user/application signal changes from StarHTML persist prehydration.

**Fix**: StarHTML dispatches a separate `starhtml:signal-source` event with source metadata for sourceful signal changes. Datastar's `datastar-signal-patch` event detail stays the vanilla signal object expected by upstream Datastar.

## Removed: Retry Current Payload

StarHTML briefly patched ordinary HTTP and network-error retries to rebuild the request payload from current signals before each retry. Datastar `1.0.1` only rebuilds request init for visibility reconnect/resume; normal retry attempts reuse the original request body/query. StarHTML now follows upstream semantics here to avoid surprising form and non-idempotent action behavior.

## Patch 4: Persist-Aware Init

**Problem**: `data-signals__ifmissing` defaults render before StarHTML persist data can restore values, causing a flash of default state.

**Fix**: In `ifMissing` signal merges, StarHTML checks cached `starhtml-persist*` storage values before applying defaults. When a persisted value is used, StarHTML emits `starhtml:signal-source` with `source: "persist"` before the Datastar patch event.

The storage scan is cached on `window.__starhtml_pc` for the lifetime of the page.
