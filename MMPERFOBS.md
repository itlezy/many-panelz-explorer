# Performance Observations — many-panelz-explorer

Archived historical performance note. Treat the bottleneck descriptions here as
point-in-time observations only; the current canonical backlog is
`docs/BACKLOG.md`.

## Why Tabs Feel Slow

### Root Cause #1 — `rebuild_root_buttons()` runs on every tab switch

**Location:** `ui/panel/navigation.py:66-92`
**Call chain:** `on_current_changed → sync_toolbar_for_current_tab → rebuild_root_controls → rebuild_root_buttons`

Every tab switch:
1. Destroys all existing drive/root buttons from the layout
2. Calls `safe_roots()` which validates each path exists on the filesystem (`stat()` calls)
3. Re-creates every button from scratch (widget allocation, fonts, tooltips, signal connections)
4. Rebuilds the layout

This is fully synchronous. On systems with many drives or network mounts, the filesystem stat calls alone can stall the UI thread.

**Fix:** Cache the root buttons and only rebuild when roots actually change (e.g., on drive add/remove events), not on every tab switch.

---

### Root Cause #2 — Column widths reapplied synchronously on every tab switch

**Location:** `ui/panel/state.py:145-149`

Resizes columns on the `QTreeView` on every tab switch, triggering layout recalculations unconditionally.

**Fix:** Track dirty state per tab — skip reapplication if column state hasn't changed since the tab was last active.

---

### Root Cause #3 — Widget map overlay repainted on every tab switch

**Location:** `ui/panel/state.py` → `widget_map_coordinator.sync_overlay()`

Overlay annotations are repainted on every switch regardless of whether anything changed.

**Fix:** Add a dirty flag — only repaint if the tab's content changed while it was inactive.

---

## Summary

| Priority | Issue | Fix |
|----------|-------|-----|
| High | Root buttons rebuilt on every tab switch | Cache buttons; rebuild only on drive change events |
| High | Filesystem stat calls on every switch | Cache `safe_roots()` result with short TTL or invalidate on volume change |
| Medium | Column widths reapplied unconditionally | Track dirty state, skip if unchanged |
| Medium | Overlay repainted unconditionally | Add dirty flag, skip if clean |

## What Is NOT a Bottleneck

- Directory loading — handled via `ThreadPoolExecutor`, non-blocking
- Tab data access — in-memory
- Model index creation — minimal work
