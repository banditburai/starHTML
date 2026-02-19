import { mergePatch, getPath, effect } from "datastar";
import { init, subscribe, getEventCount, getDataEventCount, cleanup, getEvents, buildAllowedTypes, getFilteredEvents, formatAllEventsForExport, formatSingleEventForExport, formatEventDetail, startObserving, stopObserving, CHIP_CATEGORIES, ERROR_TYPES, buildRowHtml } from "./capture.js";
import { init as init$1, cleanup as cleanup$1, subscribe as subscribe$1, getSignalCount, patchSignal, getEntries, clearPersistedData, getGroupedEntries, buildGroupHeaderHtml, buildSignalRowHtml, buildSignalDetailHtml } from "./signals.js";
import { init as init$2, cleanup as cleanup$2, subscribe as subscribe$2, getTraceCount, getFilteredTraces, buildFullTraceText, formatTraceExport, buildTraceDetailHtml, buildCopyButtonHtml, getTraceIdsInWindow, getTraceIdsInRange, formatAllTracesExport, buildTraceRowHtml } from "./timeline.js";
function setup(el, onCleanup, refs) {
  const ns = `${el._namespace}_`;
  const $ = (name) => getPath(`${ns}${name}`);
  const $set = (name, value) => mergePatch({ [`${ns}${name}`]: value });
  const effect$1 = (fn) => {
    const dispose = effect(fn);
    onCleanup(dispose);
    return dispose;
  };
  const plural = (n, word) => `${n} ${word}${n !== 1 ? "s" : ""}`;
  const setsEqual = (a, b) => a.size === b.size && [...a].every((v) => b.has(v));
  function makeScheduler(tab, render) {
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
  init();
  let _lastSeenDataCount = 0;
  const unsub = subscribe(() => {
    $set("event_count", getEventCount());
    if (!$("is_open")) {
      $set("unseen_count", getDataEventCount() - _lastSeenDataCount);
    }
  });
  onCleanup(unsub);
  try {
    const storedOpen = sessionStorage.getItem("starhtml-debug-open");
    if (storedOpen === "true") $set("is_open", true);
    const storedHeight = Number(sessionStorage.getItem("starhtml-debug-height"));
    if (storedHeight > 0) $set("panel_height", storedHeight);
    const storedTab = sessionStorage.getItem("starhtml-debug-tab");
    if (storedTab) $set("active_tab", storedTab);
  } catch {
  }
  const persistEffect = (signal, storageKey) => {
    let last = $(signal);
    effect$1(() => {
      const v = $(signal);
      if (v !== last) {
        last = v;
        try {
          sessionStorage.setItem(storageKey, String(v));
        } catch {
        }
      }
    });
  };
  persistEffect("is_open", "starhtml-debug-open");
  persistEffect("panel_height", "starhtml-debug-height");
  persistEffect("active_tab", "starhtml-debug-tab");
  let _lastIsOpen;
  effect$1(() => {
    const open = $("is_open");
    if (open === _lastIsOpen) return;
    _lastIsOpen = open;
    if (open) startObserving();
    else stopObserving();
  });
  onCleanup(cleanup);
  let _lastPadding = "";
  effect$1(() => {
    const padding = $("is_open") ? `${$("panel_height")}px` : "";
    if (padding === _lastPadding) return;
    _lastPadding = padding;
    document.documentElement.style.paddingBottom = padding;
  });
  onCleanup(() => {
    document.documentElement.style.paddingBottom = "";
  });
  effect$1(() => {
    if ($("is_open")) {
      $set("unseen_count", 0);
      _lastSeenDataCount = getDataEventCount();
    }
  });
  const flashTimers = /* @__PURE__ */ new WeakMap();
  function flashCopied(btn, label) {
    clearTimeout(flashTimers.get(btn));
    btn.textContent = "Copied!";
    flashTimers.set(
      btn,
      window.setTimeout(() => {
        btn.textContent = label;
      }, 1500)
    );
  }
  function copyText(text) {
    return navigator.clipboard.writeText(text).catch(() => {
    });
  }
  const SCROLL_BOTTOM_THRESHOLD = 20;
  let lastRenderedIds = [];
  let needsFullRender = true;
  let userAtBottom = true;
  let activeTypeFilters = /* @__PURE__ */ new Set(["signals", "elements", "script"]);
  const eventListEl = refs("event_list");
  const eventCountLabel = refs("event_count_label");
  const copyAllBtn = refs("copy_all_btn");
  const clearEventsBtn = refs("clear_events_btn");
  const errorBadgeEl = refs("error_count_badge");
  const tabContentEl = refs("tab_content");
  const jumpBtn = refs("jump_btn");
  if (tabContentEl) {
    tabContentEl.addEventListener("scroll", () => {
      userAtBottom = tabContentEl.scrollTop + tabContentEl.clientHeight >= tabContentEl.scrollHeight - SCROLL_BOTTOM_THRESHOLD;
    });
  }
  const chipRefs = {
    signals: refs("chip_signals"),
    elements: refs("chip_elements"),
    script: refs("chip_script"),
    lifecycle: refs("chip_lifecycle")
  };
  effect$1(() => {
    const newFilters = /* @__PURE__ */ new Set();
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
      const evts = getEvents();
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
      const allowedTypes = buildAllowedTypes(activeTypeFilters);
      const filtered = getFilteredEvents(
        $("visible_since_id"),
        allowedTypes,
        $("filter_text")
      );
      copyText(formatAllEventsForExport(filtered));
      flashCopied(copyAllBtn, "Copy All");
    });
  }
  if (eventListEl) {
    eventListEl.addEventListener("click", (e) => {
      const target = e.target;
      const copyBtn = target.closest(".copy-btn[data-copy-eid]");
      if (copyBtn) {
        e.stopPropagation();
        const eid2 = Number(copyBtn.dataset.copyEid);
        const evts = getEvents();
        const found = evts.find((x) => x.id === eid2);
        if (!found) return;
        copyText(formatSingleEventForExport(found));
        flashCopied(copyBtn, "Copy");
        return;
      }
      const row = target.closest(".event-row");
      if (!row) return;
      const eid = Number(row.dataset.eid);
      const wasExpanded = $("expanded_id") === eid;
      const prevExpandedId = $("expanded_id");
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
        const evts = getEvents();
        const ev = evts.find((x) => x.id === eid);
        if (ev) {
          const detail = document.createElement("div");
          detail.className = "event-detail";
          detail.innerHTML = `<button class="copy-btn" data-copy-eid="${ev.id}">Copy</button>${formatEventDetail(ev)}`;
          row.insertAdjacentElement("afterend", detail);
        }
      }
    });
  }
  const scheduleRender = makeScheduler("sse", renderSSETab);
  function renderSSETab() {
    if (!eventListEl) return;
    const allowedTypes = buildAllowedTypes(activeTypeFilters);
    const filtered = getFilteredEvents(
      $("visible_since_id"),
      allowedTypes,
      $("filter_text")
    );
    const visible = getFilteredEvents($("visible_since_id"), null, "");
    const typeCounts = /* @__PURE__ */ new Map();
    for (const ev of visible) {
      typeCounts.set(ev.type, (typeCounts.get(ev.type) ?? 0) + 1);
    }
    for (const chip of CHIP_CATEGORIES) {
      const count = chip.types.reduce((sum, t) => sum + (typeCounts.get(t) ?? 0), 0);
      const chipEl = chipRefs[chip.key];
      if (chipEl)
        chipEl.textContent = `${chip.label[0].toUpperCase()}${chip.label.slice(1)} (${count})`;
    }
    if (eventCountLabel) {
      eventCountLabel.textContent = plural(filtered.length, "event");
    }
    if (errorBadgeEl) {
      const errorCount = filtered.filter((ev) => ERROR_TYPES.has(ev.type)).length;
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
          for (const ev of newEvents) appendHtml += buildRowHtml(ev);
          eventListEl.insertAdjacentHTML("beforeend", appendHtml);
          lastRenderedIds = filteredIds;
          if (wasAtBottom && tabContentEl) tabContentEl.scrollTop = tabContentEl.scrollHeight;
          $set("show_jump_btn", !userAtBottom && filtered.length > 0);
        }
        return;
      }
    }
    $set("expanded_id", -1);
    let html = "";
    for (const ev of filtered) html += buildRowHtml(ev);
    eventListEl.innerHTML = html;
    lastRenderedIds = filteredIds;
    needsFullRender = false;
    if (wasAtBottom && tabContentEl) tabContentEl.scrollTop = tabContentEl.scrollHeight;
    $set("show_jump_btn", !userAtBottom && filtered.length > 0);
  }
  effect$1(() => {
    void $("event_count");
    void $("filter_text");
    void $("visible_since_id");
    if ($("is_open") && $("active_tab") === "sse") scheduleRender();
  });
  let _lastFilterText = $("filter_text");
  let _lastVisibleSinceId = $("visible_since_id");
  effect$1(() => {
    const ft = $("filter_text");
    const vsid = $("visible_since_id");
    if (ft !== _lastFilterText || vsid !== _lastVisibleSinceId) {
      _lastFilterText = ft;
      _lastVisibleSinceId = vsid;
      needsFullRender = true;
    }
  });
  const resizeHandle = refs("resize_handle");
  const tabBar = refs("tab_bar");
  const startResize = (e) => {
    const startY = e.clientY;
    const startH = $("panel_height");
    const onMove = (me) => {
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
  if (tabBar) {
    tabBar.addEventListener("mousedown", (e) => {
      if (e.target.closest(".tab-btn")) return;
      startResize(e);
    });
  }
  const onKeydown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.code === "Period") {
      e.preventDefault();
      $set("is_open", !$("is_open"));
    }
  };
  document.addEventListener("keydown", onKeydown);
  onCleanup(() => document.removeEventListener("keydown", onKeydown));
  const debuggerNs = el._namespace;
  let debuggerSignalNames = [];
  try {
    const parsed = JSON.parse(el.getAttribute("data-signals") || "{}");
    const prefix = `${debuggerNs}_`;
    debuggerSignalNames = Object.keys(parsed).map(
      (k) => k.startsWith(prefix) ? k.slice(prefix.length) : k
    );
  } catch {
  }
  init$1(debuggerNs, debuggerSignalNames, () => $("is_open"));
  onCleanup(cleanup$1);
  const signalListEl = refs("signal_list");
  const signalCountLabel = refs("signal_count_label");
  const signalTabCount = refs("signal_tab_count");
  const signalEmpty = refs("signal_empty");
  const clearPersistBtn = refs("clear_persist_btn");
  const collapsedGroups = /* @__PURE__ */ new Set();
  let groupsInitialized = false;
  let editingPath = "";
  let editingPending = false;
  const signalUnsub = subscribe$1(() => {
    const totalCount = getSignalCount();
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
  function getLiveEntry(path) {
    const entry = getEntries().get(path);
    return entry?.status === "live" ? entry : void 0;
  }
  function commitInput(path, value) {
    const entry = getLiveEntry(path);
    if (!entry) return;
    if (entry.type === "number") {
      const n = Number(value);
      if (!Number.isNaN(n)) patchSignal(path, n);
    } else {
      patchSignal(path, value);
    }
  }
  function renderSignalsTab() {
    if (!signalListEl) return;
    if (editingPath) {
      editingPending = true;
      return;
    }
    const groups = getGroupedEntries($("signal_filter"));
    const totalCount = getSignalCount();
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
      html += buildGroupHeaderHtml(group, isCollapsed);
      if (!isCollapsed) {
        for (const entry of group.entries) {
          html += buildSignalRowHtml(entry);
          if ($("signal_expanded_path") === entry.path) {
            html += buildSignalDetailHtml(entry);
          }
        }
      }
    }
    signalListEl.innerHTML = html;
  }
  if (signalListEl) {
    signalListEl.addEventListener("click", (e) => {
      const target = e.target;
      const toggleBtn = target.closest(".signal-toggle-btn");
      if (toggleBtn) {
        e.stopPropagation();
        const path = toggleBtn.dataset.editPath ?? "";
        const entry = getLiveEntry(path);
        if (entry) {
          patchSignal(path, !entry.value);
          renderSignalsTab();
        }
        return;
      }
      const editBtn = target.closest(".signal-edit-obj-btn");
      if (editBtn) {
        e.stopPropagation();
        const path = editBtn.dataset.editPath;
        const entry = path ? getEntries().get(path) : void 0;
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
            patchSignal(path, parsed, entry.value);
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
        textarea.addEventListener("blur", (e2) => {
          if (!editingPath) return;
          const related = e2.relatedTarget;
          if (related && (related.classList.contains("signal-edit-save") || related.classList.contains("signal-edit-cancel")))
            return;
          finishEditing();
        });
        return;
      }
      const header = target.closest(".signal-group-header");
      if (header) {
        const groupNs = header.dataset.ns ?? "";
        if (collapsedGroups.has(groupNs)) collapsedGroups.delete(groupNs);
        else collapsedGroups.add(groupNs);
        renderSignalsTab();
        return;
      }
      const row = target.closest(".signal-row");
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
      const row = e.target.closest(".signal-row");
      if (!row) return;
      const path = row.dataset.path;
      if (!path) return;
      const entry = getEntries().get(path);
      if (!entry || entry.status !== "live") return;
      $set("signal_expanded_path", path);
      if (entry.type === "boolean") {
        patchSignal(path, !entry.value);
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
    signalListEl.addEventListener("focusin", (e) => {
      const input = e.target.closest(
        ".signal-detail-input"
      );
      if (input) editingPath = input.dataset.editPath || "";
    });
    signalListEl.addEventListener("focusout", (e) => {
      const input = e.target.closest(
        ".signal-detail-input"
      );
      if (!input) return;
      if (input.dataset.editPath) commitInput(input.dataset.editPath, input.value);
      finishEditing();
    });
    signalListEl.addEventListener("keydown", (ke) => {
      const input = ke.target.closest(
        ".signal-detail-input"
      );
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
      const input = e.target.closest(
        ".signal-detail-input"
      );
      if (!input) return;
      const path = input.dataset.editPath ?? "";
      const entry = getLiveEntry(path);
      if (entry?.type === "number") {
        const n = Number(input.value);
        if (!Number.isNaN(n)) patchSignal(path, n);
      }
    });
  }
  if (clearPersistBtn) {
    clearPersistBtn.addEventListener("click", () => {
      clearPersistedData();
      clearPersistBtn.textContent = "Cleared!";
      setTimeout(() => {
        clearPersistBtn.textContent = "Clear Persisted";
      }, 1500);
    });
  }
  effect$1(() => {
    void $("signal_count");
    void $("signal_filter");
    void $("signal_expanded_path");
    if ($("is_open") && $("active_tab") === "signals") scheduleSignalRender();
  });
  init$2();
  onCleanup(cleanup$2);
  const timelineListEl = refs("timeline_list");
  const timelineCountLabel = refs("timeline_count_label");
  const timelineTabCount = refs("timeline_tab_count");
  const timelineEmpty = refs("timeline_empty");
  const timelineContentEl = refs("timeline_content");
  const tlJumpBtn = refs("tl_jump_btn");
  let timelineUserAtBottom = true;
  let tlNeedsFullRender = false;
  let lastRenderedTraceKeys = [];
  let activeTlChips = /* @__PURE__ */ new Set(["user", "sse", "signal", "warning"]);
  if (timelineContentEl) {
    timelineContentEl.addEventListener("scroll", () => {
      timelineUserAtBottom = timelineContentEl.scrollTop + timelineContentEl.clientHeight >= timelineContentEl.scrollHeight - SCROLL_BOTTOM_THRESHOLD;
    });
  }
  const timelineUnsub = subscribe$2(() => {
    const total = getTraceCount();
    $set("timeline_count", total);
    if (timelineTabCount) {
      const filtered = getFilteredTraces($("timeline_filter"), activeTlChips);
      timelineTabCount.textContent = filtered.length > 0 ? `(${filtered.length})` : "";
    }
    if ($("is_open") && $("active_tab") === "timeline") scheduleTimelineRender();
  });
  onCleanup(timelineUnsub);
  const scheduleTimelineRender = makeScheduler("timeline", renderTimelineTab);
  function renderTimelineTab() {
    if (!timelineListEl) return;
    const filtered = getFilteredTraces($("timeline_filter"), activeTlChips);
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
    const filteredKeys = filtered.map((t) => `${t.traceId}:${t.eventCount}${t.status[0]}`);
    if (!tlNeedsFullRender && filteredKeys.length >= lastRenderedTraceKeys.length) {
      const canIncrement = lastRenderedTraceKeys.every((key, i) => key === filteredKeys[i]);
      if (canIncrement) {
        if (filteredKeys.length > lastRenderedTraceKeys.length) {
          const newTraces = filtered.slice(lastRenderedTraceKeys.length);
          let appendHtml = "";
          for (const t of newTraces) appendHtml += buildTraceRowHtml(t);
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
    for (const t of filtered) html += buildTraceRowHtml(t);
    timelineListEl.innerHTML = html;
    lastRenderedTraceKeys = filteredKeys;
    tlNeedsFullRender = false;
    if (wasAtBottom && timelineContentEl)
      timelineContentEl.scrollTop = timelineContentEl.scrollHeight;
    $set("show_tl_jump", !timelineUserAtBottom && filtered.length > 0);
    if (rangeStart >= 0) updateRangeHighlight();
  }
  effect$1(() => {
    const newChips = /* @__PURE__ */ new Set();
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
  effect$1(() => {
    const f = $("timeline_filter");
    if (f !== _lastTlFilter) {
      _lastTlFilter = f;
      clearRange();
      tlNeedsFullRender = true;
      scheduleTimelineRender();
    }
  });
  effect$1(() => {
    void $("timeline_count");
    if ($("is_open") && $("active_tab") === "timeline") scheduleTimelineRender();
  });
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
    for (const r of timelineListEl.querySelectorAll(".timeline-row")) {
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
        const ids = getTraceIdsInRange(rangeStart, rangeEnd);
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
      const ids = getTraceIdsInRange(rangeStart, rangeEnd);
      const md = formatAllTracesExport(ids);
      copyText(md);
      flashCopied(rangeCopyBtn, "Copy Range");
    });
  }
  if (rangeClearBtn) {
    rangeClearBtn.addEventListener("click", clearRange);
  }
  if (timelineListEl) {
    timelineListEl.addEventListener("click", (e) => {
      const target = e.target;
      const copyBtn = target.closest(".tl-copy-btn");
      if (copyBtn) {
        const tid = Number(copyBtn.dataset.copyTrace);
        if (!Number.isNaN(tid)) {
          copyText(buildFullTraceText(tid));
          flashCopied(copyBtn, "Copy");
        }
        return;
      }
      const rowCopy = target.closest(".tl-row-copy");
      if (rowCopy) {
        const tid = Number(rowCopy.dataset.copySingle);
        if (!Number.isNaN(tid)) {
          copyText(formatTraceExport(tid));
          flashCopied(rowCopy, "⎘");
        }
        return;
      }
      const domToggle = target.closest(".tl-dom-toggle");
      if (domToggle) {
        const body = domToggle.nextElementSibling;
        if (body instanceof HTMLElement && body.classList.contains("tl-dom-body")) {
          const isOpen = body.style.display !== "none";
          body.style.display = isOpen ? "none" : "";
          domToggle.classList.toggle("open", !isOpen);
        }
        return;
      }
      const row = target.closest(".timeline-row");
      if (!row) return;
      const traceId = Number(row.dataset.traceId);
      if (Number.isNaN(traceId)) return;
      if (e.shiftKey) {
        e.preventDefault();
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
      for (const r of timelineListEl.querySelectorAll(".timeline-row")) {
        r.classList.toggle(
          "tl-row-expanded",
          Number(r.dataset.traceId) === $("timeline_expanded_id")
        );
      }
      if (!isExpanded) {
        const detail = document.createElement("div");
        detail.className = "tl-expanded";
        detail.innerHTML = buildTraceDetailHtml(traceId) + buildCopyButtonHtml(traceId);
        row.after(detail);
      }
    });
  }
  const tlExportBtn = refs("tl_export_btn");
  const tlExportMenu = refs("tl_export_menu");
  if (tlExportBtn && tlExportMenu) {
    tlExportBtn.addEventListener("click", () => {
      tlExportMenu.classList.toggle("open");
    });
    el.addEventListener("click", (e) => {
      const inExport = e.composedPath().some((n) => n instanceof HTMLElement && n.classList.contains("tl-export-wrap"));
      if (!inExport) tlExportMenu.classList.remove("open");
    });
    const exportTraces = (ids) => {
      if (ids.length === 0) return;
      copyText(formatAllTracesExport(ids));
      flashCopied(tlExportBtn, "Export ▾");
      tlExportMenu.classList.remove("open");
    };
    for (const [ref, secs] of [
      ["tl_exp_5s", 5],
      ["tl_exp_15s", 15],
      ["tl_exp_30s", 30],
      ["tl_exp_60s", 60]
    ]) {
      const btn = refs(ref);
      if (btn)
        btn.addEventListener("click", () => exportTraces(getTraceIdsInWindow(secs)));
    }
    const expAll = refs("tl_exp_all");
    if (expAll)
      expAll.addEventListener("click", () => {
        const ids = getFilteredTraces($("timeline_filter"), activeTlChips).map((t) => t.traceId);
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
export {
  setup
};
