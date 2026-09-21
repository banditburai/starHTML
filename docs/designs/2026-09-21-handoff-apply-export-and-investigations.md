# Handoff: after the Datastar 1.0.4 / StarElements adoption work (prepared 2026-09-21, evening)

Supersedes the morning handoff ("StarHTML after the Datastar 1.0.4 bump"). Items 1-4 of that checklist are done;
its optional item 5 (upstream `apply` export) is investigated and reduced to one ask (below).

## Revisions (all verified to exist)

| Repo | Branch | HEAD | Pushed? |
| --- | --- | --- | --- |
| ~/Code/sandbox/starhtml-upstream | `chore/datastar-1.0.2` | 6abd874 | yes — PR https://github.com/banditburai/starHTML/pull/85 (open, base `main`) |
| ~/Code/sandbox/starelements | `feat/star-chart-element` | e9f23a7 (12 commits since a7b867d: 1a30122 … e9f23a7) | **no** — sits on the chart feature branch; decide whether to push here or cherry-pick onto a `feat/datastar-1.0.4-adoption` branch |
| ~/Code/sandbox/starcss | `main` | 6c8bd96 (no remote) | n/a |

Uncommitted in starhtml-upstream, owner's WIP, never swept into other commits: `src/starhtml/plugins.py` +
`tests/unit/test_plugins.py` (staged; clipboard plugin uses `mergePatch`), `src/starhtml/utils.py` (get_key via
O_EXCL), `uv.lock`. Ask the owner before committing. `.git/hooks/pre-commit` was renamed to
`pre-commit.stale-beads` (stale `bd sync` hook); delete it or restore as you prefer.

Consumers: StarHTML's `debug`/`demo` extras still install StarElements 0.1.1 from PyPI, so none of the runtime
changes reach a normal install until StarElements is released (bump + `uv build`; the hatch hook compiles the JS).

## Verified state and exact commands

```
# StarHTML (both editables are REQUIRED: a bare --with-editable ../starelements resolves a cached starhtml wheel with stale JS)
cd ~/Code/sandbox/starhtml-upstream
bun run build                                               # rebuilds patched datastar-core.js + datastar.js (gitignored)
uv run --with playwright --with-editable ../starelements --with-editable . pytest tests/browser -q -p no:cacheprovider
#   -> test_starelements.py 20 passed; test_datastar_runtime_migration.py 45 passed; compat file 1 xfailed (run files separately if the
#      combined run exceeds 10 min: it did once today while a syntax error in the served wrapper made every wait time out)
uv run --with-editable ../starelements --with-editable . pytest tests/unit tests/integration -q      # 1752 passed, 1 flaky
#   (tests/unit/test_get_key_hardening.py::test_generate_new_does_not_clobber_concurrent_writers is flaky; test_devtools_* need starelements)
# StarElements
cd ~/Code/sandbox/starelements
uv run python scripts/build.py                              # compiles typescript/starelements.ts -> static/*.js (gitignored)
uv run --with pytest python -m pytest -q                    # 255 passed (plain `uv run pytest` picks a Homebrew py3.14 pytest: wrong env)
# StarCSS
cd ~/Code/sandbox/starcss && uv run pytest -q               # 116 passed
```

## Durable decisions (where recorded)

- starhtml `docs/designs/2026-09-21-datastar-1.0.4-integration.md` (addenda: review pass, patch modes, final
  boot/scan contract), `docs/designs/2026-09-21-rocket-vs-starelements.md`. docs/ is gitignored; force-added.
- starelements `docs/designs/2026-09-21-patch-scoping-and-apply-export.md` (mode table, pre-scope decision,
  the `apply` investigation with a draft upstream issue, and the Final section with the critique outcome +
  measurements). Also force-added.
- Memory: `starelements-boot-scan-contract`, `starelements-browser-harness`, `datastar-same-element-attr-order`.

Contract in one breath: StarElements defines after DOMContentLoaded + one macrotask (ordered after Datastar's
first-scan timer by the static import); light-DOM hosts are never scanned explicitly (document observer); shadow
roots call `apply(shadowRoot, true)` which StarHTML's `shadow-dom-scan` patch exports; SSE fragments are
pre-scoped in a `window`-capture `datastar-fetch` listener for every mode, with the upstream
`datastar-scope-children` hook as fallback/wipe recovery. The `datastar:scan` event and the wrapper `ready`
promise no longer exist.

## Next vertical slices, in order

1. **File the upstream Datastar issue** (draft text is in the starelements design record, "Draft upstream
   issue"; trim to the one remaining ask — export `apply`/`applyElement` from `bundles/datastar.ts` — and
   mention: `observedRoots` is add-only (`engine/engine.ts:47,235,255`), and `<script>` in patched fragments
   executes twice, see slice 3). Repo: https://github.com/starfederation/datastar. Reference clone (temp):
   `/Users/firefly/.claude/jobs/7c9d35dd/tmp/datastar` — recreate with
   `git clone --depth 1 --branch v1.0.4 https://github.com/starfederation/datastar`. When upstream ships the
   export: delete operation 2 of the `shadow-dom-scan` patch in `patches/patch_definitions.py` (the
   `let _ap=…export{_ap as apply,` line) and its marker; StarElements needs no change (it imports `apply` and
   warns `ScanUnavailable` when absent). Verify with `tests/browser/test_datastar_runtime_migration.py::
   test_datastar_scan_binds_shadow_root` (now calls `window.__datastar.apply`).

2. **Investigate: the component runtime gates all page reactivity.** Finding (perf reviewer, probe E-ii): a
   `star_app()` page with a registered StarElements component serves no Datastar `<script>` tag, only
   `<link rel=modulepreload href=/_pkg/starhtml/datastar-core.js>` plus `<script type=module
   src=/_pkg/starelements/starelements.min.js>`; Datastar evaluates only as a dependency of the component
   runtime, so delaying that script by 2 s delayed `datastar-ready` and every page-level binding by 2 s.
   Start at `src/starhtml/core.py` ~208-225 (`_datastar_url`, hdrs emission) and `register()` ~610-660 (import
   map merge drops the datastar.js script when a package registers: line ~650 filters `h.src.endswith(
   "datastar.js")`). Acceptance: with a component registered, the page carries its own
   `<script type=module src=/_pkg/starhtml/datastar.js>` (or equivalent) so a slow/failed component runtime
   delays only components; add a browser test that delays the starelements route by ~1 s (page.route with
   `await asyncio.sleep`) and asserts a page-level `data-text` renders before the host is defined. Check the
   boot gate still holds (StarElements' macrotask must still order after Datastar's first-scan timer — it does
   as long as StarElements statically imports `datastar`, regardless of who loaded Datastar first). Probe
   harness: `/Users/firefly/.claude/jobs/7c9d35dd/tmp/critique-perf/probe_e2.py` (temp; the pattern is the
   `served()` helper in `tests/browser/test_starelements.py`).

3. **Investigate: `<script>` in a patched fragment executes twice** on a plain StarHTML page with no
   StarElements loaded (perf reviewer, probe C: `window.__ran === 2`). Suspects, in order: the vendored bundle's
   patch-elements watcher runs `execute(target)` after morph (`plugins/watchers/patchElements.ts` ~`execute`)
   *and* StarHTML's `execute_script()` helper appends with `data-effect="el.remove()"`; or the StarHTML
   `outside-race-fix`/`shadow-dom-scan` patches; or Datastar itself (compare against vanilla
   `patches/datastar-upstream.js` using the `datastar_upstream_source` fixture in
   `tests/browser/test_datastar_runtime_migration.py`). Acceptance: a browser test patching
   `<script>window.__ran=(window.__ran||0)+1</script>` via `elements(..., mode="inner")` asserts `__ran === 1`
   on both the patched and vanilla bundles; if vanilla also runs it twice, it goes into the upstream issue
   from slice 1 instead of a StarHTML fix. Reproducer: `/Users/firefly/.claude/jobs/7c9d35dd/tmp/critique-perf/probe_c.py` (temp).

4. Release StarElements (see Consumers above) and re-run the StarCSS gallery CDP (`cd examples/starui &&
   uv run python app.py &` then `uv run --with websocket-client python tests/browser/gallery_cdp.py light|dark`
   from the StarCSS root; last run 0 console errors, both themes, before the StarElements runtime changes —
   the gallery does not use StarElements, so this is a regression check only).

## Known risks / unexercised

- `set_timeout(..., store=Local)` emits `$$$name` (already wrong before `Local._id` became `$$name`); no test.
- Pre-scope handles only the html namespace; Trusted Types enforcement would break `template.innerHTML`.
- `observedRoots` retention for shadow-host churn remains (upstream); light hosts no longer enter it.
- Renaming a `data-computed:` key leaves the old computed in Datastar's store (upstream: no cleanup).
- The first-scan regression test asserts `datastar-ready` fired exactly once; host-before-timeout ordering is
  no longer relied on by the runtime.
- `view_transition_selector=` yields no transition on Firefox/WebKit (Datastar 1.0.3); CSP mode: inline
  `style=` writes are not nonce-able; devtools panel under CSP unit-stamped only. (Carried over.)

Suggested skills next session: research-decision (slices 2-3), tdd-vertical-slice (the fixes), review-project-change before merging PR #85.
