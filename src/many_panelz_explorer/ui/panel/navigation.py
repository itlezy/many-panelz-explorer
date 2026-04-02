"""Navigation coordination for a single explorer panel."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QActionGroup
from PySide6.QtWidgets import QLabel, QMenu, QPushButton, QSizePolicy
from threep_commons.fs_paths import (
    coerce_path,
    dedup_paths,
    display_path_text,
    is_drive_root,
    is_path_under_root,
    normalize_windows_path_text,
    path_key,
)

from ...file_icons import FILE_ICON_MODE_NONE, shared_file_icon_resolver

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6.QtWidgets import QWidget

    from ...explorer_tab import ExplorerTab
    from ...panel_widget import PanelWidget


_SAFE_ROOTS_CACHE_TTL_SECONDS = 1.0


@dataclass(slots=True)
class _RootPathCacheEntry:
    """Store one short-lived existing-root cache entry."""

    expires_at: float
    paths: list[Path]


def _navigation_root_text(path: Path | str) -> str:
    candidate = coerce_path(path)
    if is_drive_root(candidate):
        return candidate.drive
    if os.name == "nt":
        name = candidate.name.strip()
        if name:
            return name
    return display_path_text(candidate)


def _root_picker_action_text(index: int, root_path: Path) -> str:
    label = _navigation_root_text(root_path)
    mnemonic_index = index + 1
    if 1 <= mnemonic_index <= 9:
        return f"&{mnemonic_index} {label}"
    return label


class PanelNavigationCoordinator:
    """Drive root selection, history movement, and address-bar flow."""

    def __init__(
        self,
        panel: PanelWidget,
        *,
        entry_hidden_system_flags: Callable[[os.DirEntry[str]], tuple[bool, bool]],
    ) -> None:
        self.panel = panel
        self._entry_hidden_system_flags = entry_hidden_system_flags
        self._existing_roots_cache: dict[tuple[str, ...], _RootPathCacheEntry] = {}
        self._root_buttons_signature: tuple[str, ...] | None = None
        self._root_combo_signature: tuple[str, ...] | None = None
        self._root_buttons_icon_mode: str | None = None
        self._root_combo_icon_mode: str | None = None

    def rebuild_root_controls(self, current_path: Path | None) -> None:
        roots = self.safe_roots(current_path)
        self.panel.set_root_paths(roots)
        self.rebuild_root_buttons(current_path, roots)
        self.rebuild_root_combo(current_path, roots)
        self.rebuild_breadcrumbs(current_path)

    def rebuild_root_buttons(
        self, current_path: Path | None, roots: list[Path]
    ) -> None:
        active_root_index = self.resolve_active_root_index(current_path, roots)
        roots_signature = self._root_signature(roots)
        current_icon_mode = self.panel.file_icon_mode
        if (
            self._root_buttons_signature == roots_signature
            and self._root_buttons_icon_mode == current_icon_mode
            and len(self.panel.root_buttons) == len(roots)
        ):
            self._sync_root_button_checks(active_root_index)
            return

        self._clear_root_buttons()
        self.panel.root_buttons = []
        for index, root_path in enumerate(roots):
            button = QPushButton(_navigation_root_text(root_path))
            button.setFont(self.panel.navigation_font)
            button.setMinimumWidth(0)
            button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            button.setToolTip(display_path_text(root_path))
            button.setCheckable(True)
            button.setChecked(index == active_root_index)
            if current_icon_mode != FILE_ICON_MODE_NONE:
                button.setIcon(
                    shared_file_icon_resolver().icon_for_path(
                        root_path,
                        is_dir=True,
                        mode=current_icon_mode,
                    )
                    or button.icon()
                )
            button.clicked.connect(self._navigate_to_root_callback(root_path))
            button.installEventFilter(self.panel.focus_watcher)
            self.panel.root_buttons_layout.addWidget(button)
            self.panel.root_buttons.append(button)

        self.panel.root_buttons_layout.addStretch(1)
        self._root_buttons_signature = roots_signature
        self._root_buttons_icon_mode = current_icon_mode

    def rebuild_root_combo(self, current_path: Path | None, roots: list[Path]) -> None:
        self.panel.root_combo.setVisible(self.panel.show_root_dropdown_enabled)
        if not self.panel.show_root_dropdown_enabled:
            return

        active_root_index = self.resolve_active_root_index(current_path, roots)
        roots_signature = self._root_signature(roots)
        if (
            self._root_combo_signature == roots_signature
            and self._root_combo_icon_mode == self.panel.file_icon_mode
            and self.panel.root_combo.count() == len(roots)
        ):
            self.panel.root_combo.setCurrentIndex(
                active_root_index if active_root_index is not None else -1
            )
            return

        self.panel.root_combo.blockSignals(True)
        try:
            self.panel.root_combo.clear()
            current_icon_mode = self.panel.file_icon_mode
            for root_path in roots:
                item_text = _navigation_root_text(root_path)
                if current_icon_mode == FILE_ICON_MODE_NONE:
                    self.panel.root_combo.addItem(item_text, str(root_path))
                else:
                    icon = shared_file_icon_resolver().icon_for_path(
                        root_path,
                        is_dir=True,
                        mode=current_icon_mode,
                    )
                    if icon is None:
                        self.panel.root_combo.addItem(item_text, str(root_path))
                    else:
                        self.panel.root_combo.addItem(icon, item_text, str(root_path))
                combo_idx = self.panel.root_combo.count() - 1
                self.panel.root_combo.setItemData(
                    combo_idx,
                    display_path_text(root_path),
                    Qt.ItemDataRole.ToolTipRole,
                )

            self.panel.root_combo.setCurrentIndex(
                active_root_index if active_root_index is not None else -1
            )
        finally:
            self.panel.root_combo.blockSignals(False)
        self._root_combo_signature = roots_signature
        self._root_combo_icon_mode = self.panel.file_icon_mode

    def safe_roots(self, current_path: Path | None) -> list[Path]:
        try:
            provided_roots = [
                coerce_path(p) for p in self.panel.provided_roots(current_path)
            ]
        except Exception:
            provided_roots = []
        roots = self.existing_unique_paths(provided_roots)
        if not roots:
            roots = self.fallback_roots(current_path)
        return sorted(
            roots,
            key=lambda p: (
                _navigation_root_text(p).lower(),
                display_path_text(p).lower(),
            ),
        )

    def existing_unique_paths(self, paths: list[Path]) -> list[Path]:
        cache_key = self._paths_cache_key(paths)
        if cache_key:
            cached_entry = self._existing_roots_cache.get(cache_key)
            current_time = monotonic()
            if cached_entry is not None and cached_entry.expires_at >= current_time:
                return list(cached_entry.paths)

        unique_paths = dedup_paths(paths, require_existing=True)
        if cache_key:
            self._existing_roots_cache[cache_key] = _RootPathCacheEntry(
                expires_at=monotonic() + _SAFE_ROOTS_CACHE_TTL_SECONDS,
                paths=list(unique_paths),
            )
        return unique_paths

    def fallback_roots(self, current_path: Path | None) -> list[Path]:
        candidates: list[Path] = []
        if current_path is not None:
            current = Path(current_path).expanduser()
            candidates.append(current)
            if current.anchor:
                candidates.append(Path(current.anchor))

        home = Path.home()
        candidates.append(home)
        if home.anchor:
            candidates.append(Path(home.anchor))

        root_path = Path(os.sep)
        candidates.append(root_path)

        fallback = self.existing_unique_paths(candidates)
        if fallback:
            return fallback
        return [home]

    def go_back(self) -> None:
        tab = self.panel.current_tab()
        if tab is not None:
            tab.navigation.go_back()

    def go_forward(self) -> None:
        tab = self.panel.current_tab()
        if tab is not None:
            tab.navigation.go_forward()

    def go_up(self) -> None:
        tab = self.panel.current_tab()
        if tab is not None:
            tab.navigation.go_up()

    def go_root(self) -> None:
        tab = self.panel.current_tab()
        if tab is None:
            return

        current_path = tab.navigation.path
        active_root_index = self.resolve_active_root_index(
            current_path, self.panel.root_paths
        )
        if active_root_index is not None:
            tab.navigation.set_path(self.panel.root_paths[active_root_index])
            return

        if current_path.anchor:
            tab.navigation.set_path(Path(current_path.anchor))

    def refresh_current_path(self) -> None:
        tab = self.panel.current_tab()
        if tab is not None:
            tab.navigation.refresh()

    def on_address_submitted(self) -> None:
        tab = self.panel.current_tab()
        if tab is None:
            return

        text = self.panel.address_edit.text().strip()
        if not text:
            return
        self.panel.stop_address_completion_timer()
        self.hide_address_completion_popup()
        tab.navigation.set_path(coerce_path(normalize_windows_path_text(text)))

    def set_address_text_programmatically(self, text: str) -> None:
        self.panel.set_address_completions_enabled(False)
        try:
            self.panel.address_edit.setText(text)
        finally:
            self.panel.set_address_completions_enabled(True)
        self.panel.stop_address_completion_timer()
        self.panel.set_address_completion_suggestions([])
        self.hide_address_completion_popup()

    def schedule_address_completion_update(self, _text: str) -> None:
        if not self.panel.address_completions_enabled:
            return
        self.panel.start_address_completion_timer(
            self.panel.ADDRESS_COMPLETION_DEBOUNCE_MS
        )

    def refresh_address_completions(self) -> None:
        if (
            not self.panel.address_completions_enabled
            or not self.panel.address_edit.hasFocus()
        ):
            self.hide_address_completion_popup()
            return
        raw_text = self.panel.address_edit.text().strip()
        suggestions = self.collect_address_completion_paths(raw_text)
        self.panel.set_address_completion_suggestions(suggestions)
        if not suggestions:
            self.hide_address_completion_popup()
            return
        self.panel.show_address_completion_popup()

    def on_address_completion_activated(self, path_text: str) -> None:
        selected = str(path_text).strip()
        if not selected:
            return
        self.set_address_text_programmatically(selected)
        self.panel.address_edit.setFocus()
        self.panel.address_edit.setCursorPosition(len(selected))

    def hide_address_completion_popup(self) -> None:
        popup = self.panel.completion_popup()
        if popup is not None and popup.isVisible():
            popup.hide()

    def rebuild_breadcrumbs(self, current_path: Path | None) -> None:
        """Rebuild clickable breadcrumb buttons for the current path."""

        layout = self.panel.breadcrumb_layout
        while layout.count():
            item = layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.panel.breadcrumb_buttons = []
        if current_path is None:
            self.panel.breadcrumb_host.setToolTip("")
            return

        self.panel.breadcrumb_host.setToolTip(display_path_text(current_path))
        entries = self._breadcrumb_entries(current_path)
        for index, (label, path) in enumerate(entries):
            button = QPushButton(label)
            button.setFlat(True)
            button.setMinimumWidth(0)
            button.setSizePolicy(
                QSizePolicy.Policy.Maximum,
                QSizePolicy.Policy.Fixed,
            )
            button.setToolTip(display_path_text(path))
            button.setFont(self.panel.navigation_font)
            button.clicked.connect(self._navigate_to_root_callback(path))
            button.installEventFilter(self.panel.focus_watcher)
            layout.addWidget(button)
            self.panel.breadcrumb_buttons.append(button)
            if index >= len(entries) - 1:
                continue
            separator = QLabel(">")
            separator.setFont(self.panel.navigation_font)
            separator.setProperty("panel_breadcrumb_separator", True)
            layout.addWidget(separator)
        layout.addStretch(1)

    def collect_address_completion_paths(self, raw_text: str) -> list[str]:
        context = self.resolve_address_completion_context(raw_text)
        if context is None:
            return []
        parent_dir, prefix = context
        if not parent_dir.exists() or not parent_dir.is_dir():
            return []

        prefix_cmp = prefix.casefold()
        suggestions: list[str] = []
        try:
            with os.scandir(parent_dir) as iterator:
                for entry in iterator:
                    try:
                        is_dir = entry.is_dir(follow_symlinks=False)
                    except OSError:
                        continue
                    if not is_dir:
                        continue
                    is_hidden, is_system = self._entry_hidden_system_flags(entry)
                    if not self.panel.show_hidden_enabled and is_hidden:
                        continue
                    if not self.panel.show_system_files_enabled and is_system:
                        continue
                    name = entry.name
                    if prefix_cmp and not name.casefold().startswith(prefix_cmp):
                        continue
                    suggestions.append(display_path_text(parent_dir / name))
        except OSError:
            return []
        return sorted(set(suggestions), key=str.casefold)

    def resolve_address_completion_context(
        self, raw_text: str
    ) -> tuple[Path, str] | None:
        text = normalize_windows_path_text(str(raw_text or "").strip())
        if not text:
            return None

        base_path = coerce_path(self.panel.current_path())
        expanded = normalize_windows_path_text(os.path.expanduser(text))
        has_trailing_separator = expanded.endswith(("\\", "/"))
        candidate = coerce_path(expanded)
        if has_trailing_separator:
            parent_dir = (
                candidate if candidate.is_absolute() else (base_path / candidate)
            )
            return parent_dir.expanduser(), ""

        prefix = candidate.name
        parent_part = candidate.parent
        if candidate.is_absolute():
            parent_dir = parent_part if str(parent_part) not in {"", "."} else candidate
        else:
            parent_dir = (
                base_path
                if str(parent_part) in {"", "."}
                else (base_path / parent_part)
            )
        return parent_dir.expanduser(), prefix

    def on_root_selected(self, index: int) -> None:
        root_paths = self.panel.root_paths
        if index < 0 or index >= len(root_paths):
            return
        self.navigate_to_root(root_paths[index])

    def navigate_to_root(self, root_path: Path) -> None:
        tab = self.panel.current_tab()
        if tab is None:
            return
        tab.navigation.set_path(root_path)

    def resolve_active_root_index(
        self, current_path: Path | None, roots: list[Path]
    ) -> int | None:
        """Return one active root index, preferring the deepest matching root."""

        if current_path is None:
            return None

        active_index: int | None = None
        active_length = -1
        for index, root_path in enumerate(roots):
            if not is_path_under_root(current_path, root_path):
                continue
            root_length = len(path_key(root_path))
            if root_length > active_length:
                active_index = index
                active_length = root_length
        return active_index

    def show_history_menu(self) -> None:
        tab = self.panel.current_tab()
        if tab is None:
            return

        history_entries = tab.navigation.history
        current_index = tab.navigation.history_index
        if not history_entries:
            return

        existing_menu = self.panel.take_history_menu()
        if existing_menu is not None:
            existing_menu.close()
            existing_menu.deleteLater()

        menu = QMenu(self.panel)
        for index in range(len(history_entries) - 1, -1, -1):
            entry = history_entries[index]
            action = menu.addAction(display_path_text(entry))
            action.setToolTip(display_path_text(entry))
            action.setCheckable(True)
            action.setChecked(index == current_index)
            action.triggered.connect(self._history_index_callback(tab, index))

        self.panel.set_history_menu(menu)
        menu.popup(
            self._history_menu_anchor_widget().mapToGlobal(
                self._history_menu_anchor_widget().rect().bottomLeft()
            )
        )

    def show_bookmarks_hotlist(self) -> None:
        """Show the window bookmark hotlist from this panel."""

        bookmarks_coordinator = getattr(
            self.panel.window(),
            "bookmarks_coordinator",
            None,
        )
        if bookmarks_coordinator is not None:
            bookmarks_coordinator.show_bookmarks_hotlist()

    def show_root_picker_menu(self) -> None:
        """Show a popup menu that lets the user jump to a discovered root."""

        current_path = self.panel.current_path()
        roots = self.safe_roots(current_path)
        if not roots:
            return
        active_root_index = self.resolve_active_root_index(current_path, roots)

        existing_menu = self.panel.take_root_picker_menu()
        if existing_menu is not None:
            existing_menu.close()
            existing_menu.deleteLater()

        menu = QMenu(self.panel)
        action_group = QActionGroup(menu)
        action_group.setExclusive(True)
        for index, root_path in enumerate(roots):
            action = menu.addAction(_root_picker_action_text(index, root_path))
            action.setToolTip(display_path_text(root_path))
            action.setCheckable(True)
            action.setChecked(index == active_root_index)
            action_group.addAction(action)
            action.triggered.connect(self._navigate_to_root_callback(root_path))

        self.panel.set_root_picker_menu(menu)
        menu.popup(self.root_picker_popup_point())

    def root_picker_popup_point(self) -> QPoint:
        """Return the global popup anchor for the root-picker menu."""

        current_tab = self.panel.current_tab()
        if current_tab is not None:
            return current_tab.mapToGlobal(current_tab.rect().topLeft())
        return self.panel.tabs.mapToGlobal(self.panel.tabs.rect().topLeft())

    def _navigate_to_root_callback(self, root_path: Path) -> Callable[[bool], None]:
        """Build a callback that navigates the active tab to a root path."""

        def _handle_clicked(_checked: bool = False) -> None:
            self.navigate_to_root(root_path)

        return _handle_clicked

    def _history_index_callback(
        self,
        tab: ExplorerTab,
        index: int,
    ) -> Callable[[bool], None]:
        """Build a callback that navigates to a fixed history index."""

        def _handle_triggered(_checked: bool = False) -> None:
            tab.navigation.go_to_history_index(index)

        return _handle_triggered

    def _clear_root_buttons(self) -> None:
        """Delete all root buttons and spacer items from the toolbar host."""

        while self.panel.root_buttons_layout.count():
            item = self.panel.root_buttons_layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _sync_root_button_checks(self, active_root_index: int | None) -> None:
        """Update root-button checked state without rebuilding widgets."""

        for index, button in enumerate(self.panel.root_buttons):
            button.setChecked(index == active_root_index)

    def _root_signature(self, roots: list[Path]) -> tuple[str, ...]:
        """Return a stable signature for one sorted root list."""

        return tuple(path_key(root_path) for root_path in roots)

    def _paths_cache_key(self, paths: list[Path]) -> tuple[str, ...]:
        """Return a cache key for a path set used by root validation."""

        return tuple(sorted({path_key(path) for path in paths}))

    def _history_menu_anchor_widget(self) -> QWidget:
        """Return the widget used to anchor the history menu popup."""

        if self.panel.show_history_button and self.panel.history_btn.isVisible():
            return self.panel.history_btn
        return self.panel.address_edit

    def _breadcrumb_entries(self, path: Path) -> list[tuple[str, Path]]:
        """Return ordered `(label, path)` breadcrumb entries for one path."""

        normalized_path = Path(path)
        parts = normalized_path.parts
        if not parts:
            return [(display_path_text(normalized_path), normalized_path)]

        entries: list[tuple[str, Path]] = []
        accumulated = Path(parts[0])
        root_label = _navigation_root_text(accumulated)
        entries.append((root_label, accumulated))
        for part in parts[1:]:
            accumulated = accumulated / part
            entries.append((part, accumulated))
        return entries
