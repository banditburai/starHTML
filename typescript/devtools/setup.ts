import { getPath, mergePatch, effect as rawEffect } from "datastar";
import * as capture from "./capture";
import * as signals from "./signals";
import * as timeline from "./timeline";

type CleanupFn = (fn: () => void) => void;
type RefsFn = (name: string) => HTMLElement | null;

export function setup(
  el: HTMLElement & { _namespace: string },
  onCleanup: CleanupFn,
  refs: RefsFn
): void {
  const ns = `${el._namespace}_`;

  const $ = (name: string): any => getPath(`${ns}${name}`);
  const $set = (name: string, value: unknown) => mergePatch({ [`${ns}${name}`]: value });

  const effect = (fn: () => void) => {
    const dispose = rawEffect(fn);
    onCleanup(dispose);
    return dispose;
  };

  const plural = (n: number, word: string) => `${n} ${word}${n !== 1 ? "s" : ""}`;

  const setsEqual = (a: Set<string>, b: Set<string>) =>
    a.size === b.size && [...a].every((v) => b.has(v));

  function makeScheduler(tab: string, render: () => void) {
    let pending = false;
    return () => {
      if (pending) return;
      pending = true;
      requestAnimationFrame(() => {
        pending = false;
        if ($("is_open") && $("active_tab") === tab) render();
      });
    };
  }

  // --- Lifecycle + persistence ---

  capture.init();

  let _lastSeenDataCount = 0;
  const unsub = capture.subscribe(() => {
    $set("event_count", capture.getEventCount());
    if (!$("is_open")) {
      $set("unseen_count", capture.getDataEventCount() - _lastSeenDataCount);
    }
  });
  onCleanup(unsub);

  try {
    const storedOpen = sessionStorage.getItem("starhtml-devtools-open");
    if (storedOpen === "true") $set("is_open", true);
    const storedHeight = Number(sessionStorage.getItem("starhtml-devtools-height"));
    if (storedHeight > 0) $set("panel_height", storedHeight);
    const storedTab = sessionStorage.getItem("starhtml-devtools-tab");
    if (storedTab) $set("active_tab", storedTab);
  } catch {
    // sessionStorage may be blocked in sandboxed/private contexts
  }

  const persistEffect = (signal: string, storageKey: string) => {
    let last = $(signal);
    effect(() => {
      const v = $(signal);
      if (v !== last) {
        last = v;
        try {
          sessionStorage.setItem(storageKey, String(v));
        } catch {}
      }
    });
  };
  persistEffect("is_open", "starhtml-devtools-open");
  persistEffect("panel_height", "starhtml-devtools-height");
  persistEffect("active_tab", "starhtml-devtools-tab");

  let _lastIsOpen: unknown;
  effect(() => {
    const open = $("is_open");
    if (open === _lastIsOpen) return;
    _lastIsOpen = open;
    if (open) capture.startObserving();
    else capture.stopObserving();
  });
  onCleanup(capture.cleanup);

  let _lastPadding = "";
  effect(() => {
    const padding = $("is_open") ? `${$("panel_height")}px` : "";
    if (padding === _lastPadding) return;
    _lastPadding = padding;
    document.documentElement.style.paddingBottom = padding;
  });
  onCleanup(() => {
    document.documentElement.style.paddingBottom = "";
  });

  effect(() => {
    if ($("is_open")) {
      $set("unseen_count", 0);
      _lastSeenDataCount = capture.getDataEventCount();
    }
  });

  // --- Shared clipboard helpers ---

  const flashTimers = new WeakMap<HTMLElement, number>();
  function flashCopied(btn: HTMLElement, label: string) {
    clearTimeout(flashTimers.get(btn));
    btn.textContent = "Copied!";
    flashTimers.set(
      btn,
      window.setTimeout(() => {
        btn.textContent = label;
      }, 1500)
    );
  }

  function copyText(text: string): Promise<void> {
    return navigator.clipboard.writeText(text).catch(() => {});
  }

  // --- SSE render pipeline ---

  const SCROLL_BOTTOM_THRESHOLD = 20;
  let lastRenderedIds: number[] = [];
  let needsFullRender = true;
  let userAtBottom = true;
  let activeTypeFilters = new Set(["signals", "elements", "script"]);

  const eventListEl = refs("event_list");
  const eventCountLabel = refs("event_count_label");
  const copyAllBtn = refs("copy_all_btn");
  const clearEventsBtn = refs("clear_events_btn");
  const errorBadgeEl = refs("error_count_badge");
  const tabContentEl = refs("tab_content");
  const jumpBtn = refs("jump_btn");

  if (tabContentEl) {
    tabContentEl.addEventListener("scroll", () => {
      userAtBottom =
        tabContentEl.scrollTop + tabContentEl.clientHeight >=
        tabContentEl.scrollHeight - SCROLL_BOTTOM_THRESHOLD;
    });
  }

  const chipRefs: Record<string, HTMLElement | null> = {
    signals: refs("chip_signals"),
    elements: refs("chip_elements"),
    script: refs("chip_script"),
    lifecycle: refs("chip_lifecycle"),
  };

  // Guard: Datastar data-class:active bindings can re-trigger this effect spuriously
  effect(() => {
    const newFilters = new Set<string>();
    if ($("chip_signals_on")) newFilters.add("signals");
    if ($("chip_elements_on")) newFilters.add("elements");
    if ($("chip_script_on")) newFilters.add("script");
    if ($("chip_lifecycle_on")) newFilters.add("lifecycle");
    const changed = !setsEqual(newFilters, activeTypeFilters);
    if (changed) {
      activeTypeFilters = newFilters;
      $set("expanded_id", -1);
      needsFullRender = true;
      scheduleRender();
    }
  });

  if (clearEventsBtn) {
    clearEventsBtn.addEventListener("click", () => {
      const evts = capture.getEvents();
      const latest = evts[evts.length - 1];
      $set("visible_since_id", latest ? latest.id + 1 : 0);
      $set("expanded_id", -1);
    });
  }

  if (jumpBtn) {
    jumpBtn.addEventListener("click", () => {
      if (tabContentEl) tabContentEl.scrollTop = tabContentEl.scrollHeight;
      userAtBottom = true;
      $set("show_jump_btn", false);
    });
  }

  if (copyAllBtn) {
    copyAllBtn.addEventListener("click", () => {
      const allowedTypes = capture.buildAllowedTypes(activeTypeFilters);
      const filtered = capture.getFilteredEvents(
        $("visible_since_id") as number,
        allowedTypes,
        $("filter_text") as string
      );
      copyText(capture.formatAllEventsForExport(filtered));
      flashCopied(copyAllBtn, "Copy All");
    });
  }

  if (eventListEl) {
    eventListEl.addEventListener("click", (e) => {
      const target = e.target as HTMLElement;

      const copyBtn = target.closest(".copy-btn[data-copy-eid]") as HTMLElement | null;
      if (copyBtn) {
        e.stopPropagation();
        const eid = Number(copyBtn.dataset.copyEid);
        const evts = capture.getEvents();
        const found = evts.find((x) => x.id === eid);
        if (!found) return;
        copyText(capture.formatSingleEventForExport(found));
        flashCopied(copyBtn, "Copy");
        return;
      }

      const row = target.closest(".event-row") as HTMLElement | null;
      if (!row) return;
      const eid = Number(row.dataset.eid);
      const wasExpanded = $("expanded_id") === eid;
      const prevExpandedId = $("expanded_id") as number;
      $set("expanded_id", wasExpanded ? -1 : eid);

      if (prevExpandedId !== -1) {
        const prevRow = eventListEl.querySelector(`.event-row[data-eid="${prevExpandedId}"]`);
        if (prevRow) {
          prevRow.classList.remove("expanded");
          const prevDetail = prevRow.nextElementSibling;
          if (prevDetail?.classList.contains("event-detail")) prevDetail.remove();
        }
      }

      if (!wasExpanded) {
        row.classList.add("expanded");
        const evts = capture.getEvents();
        const ev = evts.find((x) => x.id === eid);
        if (ev) {
          const detail = document.createElement("div");
          detail.className = "event-detail";
          detail.innerHTML = `<button class="copy-btn" data-copy-eid="${ev.id}">Copy</button>${capture.formatEventDetail(ev)}`;
          row.insertAdjacentElement("afterend", detail);
        }
      }
    });
  }

  const scheduleRender = makeScheduler("sse", renderSSETab);

  function renderSSETab() {
    if (!eventListEl) return;

    const allowedTypes = capture.buildAllowedTypes(activeTypeFilters);
    const filtered = capture.getFilteredEvents(
      $("visible_since_id") as number,
      allowedTypes,
      $("filter_text") as string
    );

    const visible = capture.getFilteredEvents($("visible_since_id") as number, null, "");
    const typeCounts = new Map<string, number>();
    for (const ev of visible) {
      typeCounts.set(ev.type, (typeCounts.get(ev.type) ?? 0) + 1);
    }
    for (const chip of capture.CHIP_CATEGORIES) {
      const count = chip.types.reduce((sum, t) => sum + (typeCounts.get(t) ?? 0), 0);
      const chipEl = chipRefs[chip.key];
      if (chipEl)
        chipEl.textContent = `${chip.label[0].toUpperCase()}${chip.label.slice(1)} (${count})`;
    }

    if (eventCountLabel) {
      eventCountLabel.textContent = plural(filtered.length, "event");
    }

    if (errorBadgeEl) {
      const errorCount = filtered.filter((ev) => capture.ERROR_TYPES.has(ev.type)).length;
      if (errorCount > 0) {
        errorBadgeEl.textContent = plural(errorCount, "error");
        errorBadgeEl.style.display = "";
      } else {
        errorBadgeEl.style.display = "none";
      }
    }

    const wasAtBottom = userAtBottom;
    const filteredIds = filtered.map((ev) => ev.id);

    if (!needsFullRender && filteredIds.length >= lastRenderedIds.length) {
      const canIncrement = lastRenderedIds.every((id, i) => id === filteredIds[i]);
      if (canIncrement) {
        if (filteredIds.length > lastRenderedIds.length) {
          const newEvents = filtered.slice(lastRenderedIds.length);
          let appendHtml = "";
          for (const ev of newEvents) appendHtml += capture.buildRowHtml(ev);
          eventListEl.insertAdjacentHTML("beforeend", appendHtml);
          lastRenderedIds = filteredIds;
          if (wasAtBottom && tabContentEl) tabContentEl.scrollTop = tabContentEl.scrollHeight;
          $set("show_jump_btn", !userAtBottom && filtered.length > 0);
        }
        return;
      }
    }

    // innerHTML wipes detail divs, so reset expand state
    $set("expanded_id", -1);
    let html = "";
    for (const ev of filtered) html += capture.buildRowHtml(ev);
    eventListEl.innerHTML = html;
    lastRenderedIds = filteredIds;
    needsFullRender = false;

    if (wasAtBottom && tabContentEl) tabContentEl.scrollTop = tabContentEl.scrollHeight;
    $set("show_jump_btn", !userAtBottom && filtered.length > 0);
  }

  // $$expanded_id deliberately excluded — expand/collapse is imperative (click handler)
  effect(() => {
    void $("event_count");
    void $("filter_text");
    void $("visible_since_id");
    if ($("is_open") && $("active_tab") === "sse") scheduleRender();
  });

  // Guard against spurious fires from Datastar data-bind processing
  let _lastFilterText = $("filter_text");
  let _lastVisibleSinceId = $("visible_since_id");
  effect(() => {
    const ft = $("filter_text");
    const vsid = $("visible_since_id");
    if (ft !== _lastFilterText || vsid !== _lastVisibleSinceId) {
      _lastFilterText = ft;
      _lastVisibleSinceId = vsid;
      needsFullRender = true;
    }
  });

  // --- Resize + keyboard ---

  const resizeHandle = refs("resize_handle");
  const tabBar = refs("tab_bar");

  const startResize = (e: MouseEvent) => {
    const startY = e.clientY;
    const startH = $("panel_height") as number;
    const onMove = (me: MouseEvent) => {
      $set(
        "panel_height",
        Math.max(150, Math.min(window.innerHeight * 0.8, startH - (me.clientY - startY)))
      );
    };
    const onUp = () => {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
    };
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  };

  if (resizeHandle) resizeHandle.addEventListener("mousedown", startResize);

  // Tab bar has more grab surface than the thin resize handle
  if (tabBar) {
    tabBar.addEventListener("mousedown", (e) => {
      if ((e.target as HTMLElement).closest(".tab-btn")) return;
      startResize(e);
    });
  }

  const onKeydown = (e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.code === "Period") {
      e.preventDefault();
      $set("is_open", !$("is_open"));
    }
  };
  document.addEventListener("keydown", onKeydown);
  onCleanup(() => document.removeEventListener("keydown", onKeydown));

  // --- Signals tab ---

  const devtoolsNs = el._namespace;
  // Derive bare signal names so the filter excludes devtools' own signals
  let devtoolsSignalNames: string[] = [];
  try {
    const parsed = JSON.parse(el.getAttribute("data-signals") || "{}");
    const prefix = `${devtoolsNs}_`;
    devtoolsSignalNames = Object.keys(parsed).map((k) =>
      k.startsWith(prefix) ? k.slice(prefix.length) : k
    );
  } catch {
    // non-critical — signals exclusion will fall back to prefix-only filtering
  }
  signals.init(devtoolsNs, devtoolsSignalNames, () => $("is_open") as boolean);
  onCleanup(signals.cleanup);

  const signalListEl = refs("signal_list");
  const signalCountLabel = refs("signal_count_label");
  const signalTabCount = refs("signal_tab_count");
  const signalEmpty = refs("signal_empty");
  const clearPersistBtn = refs("clear_persist_btn");

  const collapsedGroups = new Set<string>();
  let groupsInitialized = false;
  let editingPath = "";
  let editingPending = false;

  const signalUnsub = signals.subscribe(() => {
    const totalCount = signals.getSignalCount();
    $set("signal_count", totalCount);
    if (signalCountLabel) signalCountLabel.textContent = plural(totalCount, "signal");
    if (signalTabCount) signalTabCount.textContent = totalCount > 0 ? `(${totalCount})` : "";
    if ($("is_open") && $("active_tab") === "signals") scheduleSignalRender();
  });
  onCleanup(signalUnsub);

  const scheduleSignalRender = makeScheduler("signals", renderSignalsTab);

  function finishEditing() {
    editingPath = "";
    if (editingPending) {
      editingPending = false;
      renderSignalsTab();
    }
  }

  function getLiveEntry(path: string) {
    const entry = signals.getEntries().get(path);
    return entry?.status === "live" ? entry : undefined;
  }

  function commitInput(path: string, value: string) {
    const entry = getLiveEntry(path);
    if (!entry) return;
    if (entry.type === "number") {
      const n = Number(value);
      if (!Number.isNaN(n)) signals.patchSignal(path, n);
    } else {
      signals.patchSignal(path, value);
    }
  }

  function renderSignalsTab() {
    if (!signalListEl) return;
    if (editingPath) {
      editingPending = true;
      return;
    }
    const groups = signals.getGroupedEntries($("signal_filter") as string);
    const totalCount = signals.getSignalCount();

    // Default to showing only page signals (others are debugger/component internals)
    if (!groupsInitialized && groups.length > 0) {
      groupsInitialized = true;
      for (const g of groups) {
        if (g.namespace !== "") collapsedGroups.add(g.namespace);
      }
    }

    if (signalEmpty) signalEmpty.style.display = totalCount === 0 ? "" : "none";

    let html = "";
    for (const group of groups) {
      const isCollapsed = collapsedGroups.has(group.namespace);
      html += signals.buildGroupHeaderHtml(group, isCollapsed);
      if (!isCollapsed) {
        for (const entry of group.entries) {
          html += signals.buildSignalRowHtml(entry);
          if ($("signal_expanded_path") === entry.path) {
            html += signals.buildSignalDetailHtml(entry);
          }
        }
      }
    }
    signalListEl.innerHTML = html;
  }

  if (signalListEl) {
    signalListEl.addEventListener("click", (e) => {
      const target = e.target as HTMLElement;

      const toggleBtn = target.closest(".signal-toggle-btn") as HTMLElement | null;
      if (toggleBtn) {
        e.stopPropagation();
        const path = toggleBtn.dataset.editPath ?? "";
        const entry = getLiveEntry(path);
        if (entry) {
          signals.patchSignal(path, !entry.value);
          renderSignalsTab();
        }
        return;
      }

      const editBtn = target.closest(".signal-edit-obj-btn") as HTMLElement | null;
      if (editBtn) {
        e.stopPropagation();
        const path = editBtn.dataset.editPath;
        const entry = path ? signals.getEntries().get(path) : undefined;
        if (!path || !entry) return;

        editingPath = path;
        const json = JSON.stringify(entry.value, null, 2);
        const editor = document.createElement("div");
        editor.className = "signal-json-editor";
        const textarea = document.createElement("textarea");
        textarea.className = "signal-edit-textarea";
        textarea.value = json;

        const saveBtn = document.createElement("button");
        saveBtn.className = "signal-edit-save";
        saveBtn.textContent = "Save";

        const cancelBtn = document.createElement("button");
        cancelBtn.className = "signal-edit-cancel";
        cancelBtn.textContent = "Cancel";

        const errorSpan = document.createElement("span");
        errorSpan.className = "signal-edit-error";

        const actions = document.createElement("div");
        actions.className = "signal-edit-actions";
        actions.append(saveBtn, cancelBtn, errorSpan);
        editor.append(textarea, actions);

        editBtn.replaceWith(editor);
        textarea.focus();

        saveBtn.addEventListener("click", () => {
          if (!getLiveEntry(path)) {
            finishEditing();
            return;
          }
          try {
            const parsed = JSON.parse(textarea.value);
            signals.patchSignal(path, parsed, entry.value);
            finishEditing();
          } catch {
            errorSpan.textContent = "Invalid JSON";
          }
        });
        cancelBtn.addEventListener("click", () => finishEditing());

        textarea.addEventListener("keydown", (ke) => {
          if (ke.key === "Escape") {
            ke.preventDefault();
            finishEditing();
          }
          if (ke.key === "Enter" && (ke.metaKey || ke.ctrlKey)) {
            ke.preventDefault();
            saveBtn.click();
          }
        });
        textarea.addEventListener("blur", (e) => {
          if (!editingPath) return;
          const related = e.relatedTarget as HTMLElement | null;
          if (
            related &&
            (related.classList.contains("signal-edit-save") ||
              related.classList.contains("signal-edit-cancel"))
          )
            return;
          finishEditing();
        });
        return;
      }

      const header = target.closest(".signal-group-header") as HTMLElement | null;
      if (header) {
        const groupNs = header.dataset.ns ?? "";
        if (collapsedGroups.has(groupNs)) collapsedGroups.delete(groupNs);
        else collapsedGroups.add(groupNs);
        renderSignalsTab();
        return;
      }

      const row = target.closest(".signal-row") as HTMLElement | null;
      if (row) {
        const path = row.dataset.path;
        if (path) {
          $set("signal_expanded_path", $("signal_expanded_path") === path ? "" : path);
          renderSignalsTab();
        }
        return;
      }
    });

    signalListEl.addEventListener("dblclick", (e) => {
      const row = (e.target as HTMLElement).closest(".signal-row") as HTMLElement | null;
      if (!row) return;
      const path = row.dataset.path;
      if (!path) return;
      const entry = signals.getEntries().get(path);
      if (!entry || entry.status !== "live") return;

      // Undo click's toggle from the preceding click event
      $set("signal_expanded_path", path);

      if (entry.type === "boolean") {
        signals.patchSignal(path, !entry.value);
        return;
      }

      if (entry.type === "string" || entry.type === "number") {
        editingPath = path;
        const valueSpan = row.querySelector(".signal-value");
        if (!valueSpan) return;

        const input = document.createElement("input");
        input.type = entry.type === "number" ? "number" : "text";
        input.className = "signal-edit-input";
        input.value = String(entry.value);
        valueSpan.textContent = "";
        valueSpan.appendChild(input);
        input.focus();
        input.select();

        const commit = () => {
          commitInput(path, input.value);
          finishEditing();
        };

        input.addEventListener("keydown", (ke) => {
          if (ke.key === "Enter") {
            ke.preventDefault();
            commit();
          }
          if (ke.key === "Escape") {
            ke.preventDefault();
            finishEditing();
          }
        });
        input.addEventListener("blur", () => {
          if (!editingPath) return;
          finishEditing();
        });
      }
    });

    // Pause re-renders while editing detail-panel inputs
    signalListEl.addEventListener("focusin", (e) => {
      const input = (e.target as HTMLElement).closest(
        ".signal-detail-input"
      ) as HTMLInputElement | null;
      if (input) editingPath = input.dataset.editPath || "";
    });
    signalListEl.addEventListener("focusout", (e) => {
      const input = (e.target as HTMLElement).closest(
        ".signal-detail-input"
      ) as HTMLInputElement | null;
      if (!input) return;
      if (input.dataset.editPath) commitInput(input.dataset.editPath, input.value);
      finishEditing();
    });

    signalListEl.addEventListener("keydown", (ke) => {
      const input = (ke.target as HTMLElement).closest(
        ".signal-detail-input"
      ) as HTMLInputElement | null;
      if (!input) return;
      const path = input.dataset.editPath;
      if (!path) return;
      if (ke.key === "Enter") {
        ke.preventDefault();
        commitInput(path, input.value);
        finishEditing();
      }
      if (ke.key === "Escape") {
        ke.preventDefault();
        $set("signal_expanded_path", "");
        finishEditing();
      }
    });

    signalListEl.addEventListener("input", (e) => {
      const input = (e.target as HTMLElement).closest(
        ".signal-detail-input"
      ) as HTMLInputElement | null;
      if (!input) return;
      const path = input.dataset.editPath ?? "";
      const entry = getLiveEntry(path);
      if (entry?.type === "number") {
        const n = Number(input.value);
        if (!Number.isNaN(n)) signals.patchSignal(path, n);
      }
    });
  }

  if (clearPersistBtn) {
    clearPersistBtn.addEventListener("click", () => {
      signals.clearPersistedData();
      clearPersistBtn.textContent = "Cleared!";
      setTimeout(() => {
        clearPersistBtn.textContent = "Clear Persisted";
      }, 1500);
    });
  }

  effect(() => {
    void $("signal_count");
    void $("signal_filter");
    void $("signal_expanded_path");
    if ($("is_open") && $("active_tab") === "signals") scheduleSignalRender();
  });

  // --- Timeline tab ---

  timeline.init();
  onCleanup(timeline.cleanup);

  const timelineListEl = refs("timeline_list");
  const timelineCountLabel = refs("timeline_count_label");
  const timelineTabCount = refs("timeline_tab_count");
  const timelineEmpty = refs("timeline_empty");
  const timelineContentEl = refs("timeline_content");
  const tlJumpBtn = refs("tl_jump_btn");

  let timelineUserAtBottom = true;
  let tlNeedsFullRender = false;
  let lastRenderedTraceKeys: string[] = [];
  let activeTlChips = new Set(["user", "sse", "signal", "warning"]);

  if (timelineContentEl) {
    timelineContentEl.addEventListener("scroll", () => {
      timelineUserAtBottom =
        timelineContentEl.scrollTop + timelineContentEl.clientHeight >=
        timelineContentEl.scrollHeight - SCROLL_BOTTOM_THRESHOLD;
    });
  }

  const timelineUnsub = timeline.subscribe(() => {
    const total = timeline.getTraceCount();
    $set("timeline_count", total);
    // Show filtered count so signal-only traces don't inflate badge when chip is off
    if (timelineTabCount) {
      const filtered = timeline.getFilteredTraces($("timeline_filter") as string, activeTlChips);
      timelineTabCount.textContent = filtered.length > 0 ? `(${filtered.length})` : "";
    }
    if ($("is_open") && $("active_tab") === "timeline") scheduleTimelineRender();
  });
  onCleanup(timelineUnsub);

  const scheduleTimelineRender = makeScheduler("timeline", renderTimelineTab);

  function renderTimelineTab() {
    if (!timelineListEl) return;

    const filtered = timeline.getFilteredTraces($("timeline_filter") as string, activeTlChips);

    if (timelineCountLabel) {
      timelineCountLabel.textContent = plural(filtered.length, "trace");
    }
    if (timelineTabCount) {
      timelineTabCount.textContent = filtered.length > 0 ? `(${filtered.length})` : "";
    }
    if (timelineEmpty) {
      timelineEmpty.style.display = filtered.length === 0 ? "" : "none";
    }

    const wasAtBottom = timelineUserAtBottom;
    // Fingerprint includes eventCount + status so stale rows trigger full re-render
    const filteredKeys = filtered.map((t) => `${t.traceId}:${t.eventCount}${t.status[0]}`);

    if (!tlNeedsFullRender && filteredKeys.length >= lastRenderedTraceKeys.length) {
      const canIncrement = lastRenderedTraceKeys.every((key, i) => key === filteredKeys[i]);
      if (canIncrement) {
        if (filteredKeys.length > lastRenderedTraceKeys.length) {
          const newTraces = filtered.slice(lastRenderedTraceKeys.length);
          let appendHtml = "";
          for (const t of newTraces) appendHtml += timeline.buildTraceRowHtml(t);
          timelineListEl.insertAdjacentHTML("beforeend", appendHtml);
          lastRenderedTraceKeys = filteredKeys;
          if (wasAtBottom && timelineContentEl)
            timelineContentEl.scrollTop = timelineContentEl.scrollHeight;
          $set("show_tl_jump", !timelineUserAtBottom && filtered.length > 0);
        }
        return;
      }
    }

    $set("timeline_expanded_id", -1);
    let html = "";
    for (const t of filtered) html += timeline.buildTraceRowHtml(t);
    timelineListEl.innerHTML = html;
    lastRenderedTraceKeys = filteredKeys;
    tlNeedsFullRender = false;

    if (wasAtBottom && timelineContentEl)
      timelineContentEl.scrollTop = timelineContentEl.scrollHeight;
    $set("show_tl_jump", !timelineUserAtBottom && filtered.length > 0);

    // innerHTML wipes classes, so restore range highlighting
    if (rangeStart >= 0) updateRangeHighlight();
  }

  // Guard against spurious effect re-triggers from Datastar chip bindings
  effect(() => {
    const newChips = new Set<string>();
    if ($("tl_chip_user")) newChips.add("user");
    if ($("tl_chip_sse")) newChips.add("sse");
    if ($("tl_chip_signal")) newChips.add("signal");
    if ($("tl_chip_warning")) newChips.add("warning");
    const changed = !setsEqual(newChips, activeTlChips);
    if (changed) {
      activeTlChips = newChips;
      $set("timeline_expanded_id", -1);
      clearRange();
      tlNeedsFullRender = true;
      scheduleTimelineRender();
    }
  });

  let _lastTlFilter = $("timeline_filter");
  effect(() => {
    const f = $("timeline_filter");
    if (f !== _lastTlFilter) {
      _lastTlFilter = f;
      clearRange();
      tlNeedsFullRender = true;
      scheduleTimelineRender();
    }
  });

  effect(() => {
    void $("timeline_count");
    if ($("is_open") && $("active_tab") === "timeline") scheduleTimelineRender();
  });

  // --- Shift-click range selection ---

  let rangeStart = -1;
  let rangeEnd = -1;

  const rangeBar = refs("tl_range_bar");
  const rangeLabel = refs("tl_range_label");
  const rangeCopyBtn = refs("tl_range_copy");
  const rangeClearBtn = refs("tl_range_clear");

  function updateRangeHighlight() {
    if (!timelineListEl) return;
    const lo = Math.min(rangeStart, rangeEnd);
    const hi = Math.max(rangeStart, rangeEnd);
    const hasRange = rangeStart >= 0 && rangeEnd >= 0;
    for (const r of timelineListEl.querySelectorAll<HTMLElement>(".timeline-row")) {
      const tid = Number(r.dataset.traceId);
      r.classList.toggle("tl-range-start", tid === rangeStart);
      r.classList.toggle("tl-range-end", tid === rangeEnd);
      r.classList.toggle(
        "tl-in-range",
        hasRange && tid >= lo && tid <= hi && tid !== rangeStart && tid !== rangeEnd
      );
    }
    if (rangeBar) {
      rangeBar.classList.toggle("active", hasRange);
      if (hasRange && rangeLabel) {
        const ids = timeline.getTraceIdsInRange(rangeStart, rangeEnd);
        rangeLabel.textContent = `${plural(ids.length, "trace")} selected`;
      }
    }
  }

  function clearRange() {
    rangeStart = -1;
    rangeEnd = -1;
    updateRangeHighlight();
  }

  if (rangeCopyBtn) {
    rangeCopyBtn.addEventListener("click", () => {
      if (rangeStart < 0 || rangeEnd < 0) return;
      const ids = timeline.getTraceIdsInRange(rangeStart, rangeEnd);
      const md = timeline.formatAllTracesExport(ids);
      copyText(md);
      flashCopied(rangeCopyBtn, "Copy Range");
    });
  }

  if (rangeClearBtn) {
    rangeClearBtn.addEventListener("click", clearRange);
  }

  // --- Timeline click delegation ---

  if (timelineListEl) {
    timelineListEl.addEventListener("click", (e) => {
      const target = e.target as HTMLElement;

      const copyBtn = target.closest(".tl-copy-btn") as HTMLElement | null;
      if (copyBtn) {
        const tid = Number(copyBtn.dataset.copyTrace);
        if (!Number.isNaN(tid)) {
          copyText(timeline.buildFullTraceText(tid));
          flashCopied(copyBtn, "Copy");
        }
        return;
      }

      const rowCopy = target.closest(".tl-row-copy") as HTMLElement | null;
      if (rowCopy) {
        const tid = Number(rowCopy.dataset.copySingle);
        if (!Number.isNaN(tid)) {
          copyText(timeline.formatTraceExport(tid));
          flashCopied(rowCopy, "\u2398");
        }
        return;
      }

      const domToggle = target.closest(".tl-dom-toggle") as HTMLElement | null;
      if (domToggle) {
        const body = domToggle.nextElementSibling;
        if (body instanceof HTMLElement && body.classList.contains("tl-dom-body")) {
          const isOpen = body.style.display !== "none";
          body.style.display = isOpen ? "none" : "";
          domToggle.classList.toggle("open", !isOpen);
        }
        return;
      }

      const row = target.closest(".timeline-row") as HTMLElement | null;
      if (!row) return;
      const traceId = Number(row.dataset.traceId);
      if (Number.isNaN(traceId)) return;

      if (e.shiftKey) {
        e.preventDefault(); // prevent text selection
        if (rangeStart < 0) {
          rangeStart = traceId;
        } else if (rangeEnd < 0) {
          rangeEnd = traceId;
        } else {
          rangeStart = traceId;
          rangeEnd = -1;
        }
        updateRangeHighlight();
        return;
      }

      if (rangeStart >= 0) clearRange();

      const isExpanded = $("timeline_expanded_id") === traceId;
      $set("timeline_expanded_id", isExpanded ? -1 : traceId);

      const existing = timelineListEl.querySelector(".tl-expanded");
      if (existing) existing.remove();

      for (const r of timelineListEl.querySelectorAll<HTMLElement>(".timeline-row")) {
        r.classList.toggle(
          "tl-row-expanded",
          Number(r.dataset.traceId) === $("timeline_expanded_id")
        );
      }

      if (!isExpanded) {
        const detail = document.createElement("div");
        detail.className = "tl-expanded";
        detail.innerHTML =
          timeline.buildTraceDetailHtml(traceId) + timeline.buildCopyButtonHtml(traceId);
        row.after(detail);
      }
    });
  }

  // --- Export dropdown ---

  const tlExportBtn = refs("tl_export_btn");
  const tlExportMenu = refs("tl_export_menu");

  if (tlExportBtn && tlExportMenu) {
    tlExportBtn.addEventListener("click", () => {
      tlExportMenu.classList.toggle("open");
    });
    // composedPath needed for shadow DOM event retargeting
    el.addEventListener("click", (e) => {
      const inExport = e
        .composedPath()
        .some((n) => n instanceof HTMLElement && n.classList.contains("tl-export-wrap"));
      if (!inExport) tlExportMenu.classList.remove("open");
    });

    const exportTraces = (ids: number[]) => {
      if (ids.length === 0) return;
      copyText(timeline.formatAllTracesExport(ids));
      flashCopied(tlExportBtn, "Export \u25BE");
      tlExportMenu.classList.remove("open");
    };

    for (const [ref, secs] of [
      ["tl_exp_5s", 5],
      ["tl_exp_15s", 15],
      ["tl_exp_30s", 30],
      ["tl_exp_60s", 60],
    ] as const) {
      const btn = refs(ref);
      if (btn)
        btn.addEventListener("click", () => exportTraces(timeline.getTraceIdsInWindow(secs)));
    }

    const expAll = refs("tl_exp_all");
    if (expAll)
      expAll.addEventListener("click", () => {
        const ids = timeline
          .getFilteredTraces($("timeline_filter") as string, activeTlChips)
          .map((t) => t.traceId);
        exportTraces(ids);
      });
  }

  if (tlJumpBtn) {
    tlJumpBtn.addEventListener("click", () => {
      if (timelineContentEl) timelineContentEl.scrollTop = timelineContentEl.scrollHeight;
      timelineUserAtBottom = true;
      $set("show_tl_jump", false);
    });
  }
}
