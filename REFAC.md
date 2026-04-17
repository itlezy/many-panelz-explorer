# Refactoring Notes

Archived historical engineering note. Treat file paths, line counts, and policy
violations here as point-in-time observations only. The current canonical
product backlog is `docs/BACKLOG.md`.

## Immediate Fix (Quick Win)

**3 files need `ruff format`:**
- `dialogs/settings/section_appearance_panels.py`
- `panel_widget.py`
- `ui/window/actions.py`

Run `ruff format src/` to fix them all at once.

---

## Structural Warnings (Policy Violations)

These pass CI but trigger the custom policy checker.

**Oversized files (>600 lines):**

| File | Lines |
|------|-------|
| `ui/window/actions.py` | 968 |
| `panel_widget.py` | 937 |
| `section_operations_general.py` | 732 |
| `terminal_launchers.py` | 654 |
| `settings_dialog.py` | 617 |
| `ui/window/panels.py` | 625 |
| `section_appearance_panels.py` | 625 |

**Oversized classes (>450 lines):**

| Class | Lines |
|-------|-------|
| `WindowUiComposer` | 933 |
| `PanelWidget` | 817 |
| `OpsDefaultSettingsMixin` | 532 |
| `SettingsDialog` | 534 |
| `WindowPanelsCoordinator` | 549 |
| `SettingsManager` | 502 |

**Oversized functions (>120 lines):**

| Function | Lines |
|----------|-------|
| `collect_preferences_from_controls()` | 186 |
| `load_operations_preferences()` | 172 |
| `build_panel_visibility_rows()` | 158 |
| `build_terminal_tool_rows()` | 156 |
| `set_ui_preferences()` | 148 |
| `build_menus()` | 147 |
| `_build_panel_actions()` | 138 |
| `build_panel_toolbar()` | 123 |
| `_build_view_actions()` | 123 |

Most violations are in UI/settings dialog code, which is somewhat expected but still worth breaking up.

---

## Top Suggestions

### 1. Run `ruff format src/`
Fix formatting drift in the 3 files above.

### 2. Split `WindowUiComposer` (933 lines)
Extract into separate classes:
- `ActionBuilder` — action creation and wiring
- `MenuBuilder` — menu structure
- `ShortcutBuilder` — keyboard shortcut registration

Currently the hardest component to test due to its size.

### 3. Split `PanelWidget` (817 lines)
Extract dedicated coordinators for:
- Focus management
- Toolbar building
- Tab coordination

### 4. Break down large settings functions
- `collect_preferences_from_controls()` (186 lines): extract per-field preference handlers
- `load_operations_preferences()` (172 lines): extract backend configuration loading
- `build_panel_toolbar()` (123 lines): extract per-section control builders

### 5. Verify coverage target
Coverage target is 80% but no recent report was found confirming it is being met. Run `pytest --cov` and check.
