# Datastar Vendored Patches

Vendored file: `src/starhtml/static/datastar.js`
Version tracked in `DATASTAR_VERSION` (`starapp.py`), with `+starhtml` build metadata suffix to distinguish from vanilla.

## Updating Datastar

Patches are applied automatically:

```
python scripts/update_datastar.py 1.0.0-RC.8
```

(The `v` prefix is optional — `v1.0.0-RC.8` also works.)

This downloads vanilla Datastar from CDN, applies all patches, verifies markers, and updates `DATASTAR_VERSION`.

If a patch fails (Datastar internals changed), the script saves `src/starhtml/static/datastar.vanilla.js` for diffing. Fix the search strings in `patches/patch_definitions.py`.

To verify patches on the current file:

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

**Fix**: Added a `document.addEventListener("datastar:scan", ...)` that calls Datastar's internal `nn` (scan) function on the provided root.

**Note**: The minified function name `nn` may change across versions. Look for the function that calls `_e()` on descendants and sets up a `MutationObserver`.

## Patch 2: Outside Modifier Race Fix

**Problem**: When a user gesture opens a popover (via `data-show`) and an `outside` handler fires in the same interaction, the popover opens and closes instantly. Two variants:

1. **Cross-event**: `mouseup` opens popover → `click` fires (same gesture, separate event) → outside handler closes it
2. **Same-event**: `click` opens popover → same `click` propagates to document → outside handler closes it

**Fix**: Two complementary mechanisms:

- **MutationObserver + rAF** (cross-event): Watches the element's `style` attribute. On mutation, sets a flag cleared by `requestAnimationFrame`. Outside events arriving while the flag is set are suppressed.
- **Capture-phase snapshot** (same-event): Registers a capture-phase listener for the same event type. At capture phase, snapshots whether the element is hidden (`display: none`). If it was hidden when the event started, the outside handler suppresses.

**Scope**: The `e.style.display === "none"` check only detects inline styles set by `data-show`. This is an intentional coupling — `data-show` is the primary use case for `outside` modifiers.

## Patch 3: Init Refire Fix

**Problem**: `data-init` fires twice on page load when any Datastar plugin (e.g., `persist`) is registered in a separate `<script type="module">`. Each late-arriving `attribute()` call triggers a full-page rescan via `nn()`, re-executing all already-processed bindings including `data-init`.

**Root cause**: Datastar's `nn` scan function passed a hardcoded filter flag (`!0`) to `_e()`, which told the attribute processor (`xt`) to only process newly-registered plugins. An earlier fix ("scan-timing-fix") removed this flag entirely so that shadow DOM scans would process all plugins — but this also removed the filter for plugin-registration rescans, causing the double-fire.

**Fix**: Made the filter conditional via a 3rd parameter `f` on `nn()`:

- **Plugin registration rescans** (`p()` → `nn(void 0, !0, !0)`): `f=true` → only newly-registered plugins are processed on existing elements.
- **Shadow DOM / component scans** (`datastar:scan` → `nn(root, !0)`): `f` absent → all plugins are processed (required for new DOM scopes).

This supersedes the earlier "scan-timing-fix" which was never formalized as a patch.
