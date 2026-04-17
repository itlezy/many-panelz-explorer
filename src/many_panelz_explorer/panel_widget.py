"""Panel widget that hosts navigation controls and explorer tabs."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, cast

from PySide6.QtCore import (
    QEvent,
    QObject,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QFont, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QLayout,
    QLineEdit,
    QMenu,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from threep_commons.fs_paths import display_path_text
from threep_commons.qt.widget_identity import assign_widget_identity

from . import widget_naming
from .explorer_tab import ExplorerTab
from .file_icons import ALLOWED_FILE_ICON_MODES, FILE_ICON_MODE_NONE
from .mounts import list_roots_for_navigation
from .panel_tab_positions import (
    TAB_POSITION_MODE_BOTTOM,
    TAB_POSITION_MODE_DEFAULT,
    TAB_POSITION_MODE_LEFT,
    TAB_POSITION_MODE_LEFT_HORIZONTAL,
    TAB_POSITION_MODE_RIGHT,
    TAB_POSITION_MODE_RIGHT_HORIZONTAL,
    TAB_POSITION_MODE_TOP,
    normalize_panel_tab_position_mode,
    resolve_tab_position_mode,
)
from .runtime_trace import trace_span
from .ui.panel import (
    PanelInlineFilterCoordinator,
    PanelNavigationCoordinator,
    PanelPresentationCoordinator,
    PanelStateCoordinator,
    PanelTabGroupsCoordinator,
    PanelWidgetMapCoordinator,
    assign_panel_control_identities,
    build_panel_filter,
    build_panel_tabs,
    build_panel_toolbar,
    configure_panel_shortcuts_and_timers,
    finalize_panel_ui,
    install_panel_focus_watchers,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6.QtCore import QStringListModel, QTimer
    from PySide6.QtGui import QShortcut
    from PySide6.QtWidgets import QCompleter, QHBoxLayout, QTabWidget

    from .ui.window.state_types import TabGroupState


def _tab_label(path: Path) -> str:
    anchor = path.anchor
    if anchor and path == Path(anchor):
        return display_path_text(path)
    return path.name or display_path_text(path)


def _entry_hidden_system_flags(entry: os.DirEntry[str]) -> tuple[bool, bool]:
    """Return `(is_hidden, is_system)` flags for one directory entry."""

    hidden = entry.name.startswith(".")
    if os.name != "nt":
        return hidden, False
    try:
        stat_result = entry.stat(follow_symlinks=False)
    except OSError:
        return hidden, False
    attributes = int(getattr(stat_result, "st_file_attributes", 0))
    normalized_hidden = hidden or bool(attributes & 0x2)
    system = bool(attributes & 0x4)
    return normalized_hidden, system


class _FocusWatcher(QObject):
    focused = Signal()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() in {QEvent.Type.FocusIn, QEvent.Type.MouseButtonPress}:
            self.focused.emit()
        return super().eventFilter(obj, event)


class PanelWidget(QWidget):
    """Own one pane of tabs, navigation widgets, and focus state."""

    COLUMN_SYNC_DEBOUNCE_MS = 120
    ADDRESS_COMPLETION_DEBOUNCE_MS = 140
    ROOT_COMBO_MIN_WIDTH = 108
    COLUMN_ALIGN_MODE_CURRENT_PANEL_TABS = "current_panel_tabs"
    COLUMN_ALIGN_MODE_CURRENT_WINDOW_PANELS_TABS = "current_window_panels_tabs"
    COLUMN_ALIGN_MODE_ALL_WINDOWS_PANELS_TABS = "all_windows_panels_tabs"
    COLUMN_ALIGN_MODE_NONE = "none"
    TAB_POSITION_MODE_DEFAULT = TAB_POSITION_MODE_DEFAULT
    TAB_POSITION_MODE_TOP = TAB_POSITION_MODE_TOP
    TAB_POSITION_MODE_BOTTOM = TAB_POSITION_MODE_BOTTOM
    TAB_POSITION_MODE_LEFT = TAB_POSITION_MODE_LEFT
    TAB_POSITION_MODE_LEFT_HORIZONTAL = TAB_POSITION_MODE_LEFT_HORIZONTAL
    TAB_POSITION_MODE_RIGHT = TAB_POSITION_MODE_RIGHT
    TAB_POSITION_MODE_RIGHT_HORIZONTAL = TAB_POSITION_MODE_RIGHT_HORIZONTAL

    activated = Signal()
    current_context_changed = Signal()
    column_widths_sync_requested = Signal(list, object)
    became_empty = Signal()
    focus_watcher: _FocusWatcher
    refresh_btn: QPushButton
    root_buttons_host: QWidget
    root_buttons_layout: QHBoxLayout
    root_combo: QComboBox
    group_picker_combo: QComboBox
    new_group_btn: QPushButton
    history_btn: QPushButton
    bookmarks_btn: QPushButton
    address_edit: QLineEdit
    breadcrumb_host: QWidget
    breadcrumb_layout: QHBoxLayout
    breadcrumb_buttons: list[QPushButton]
    back_btn: QPushButton
    forward_btn: QPushButton
    up_btn: QPushButton
    root_btn: QPushButton
    navigation_buttons: list[QPushButton]
    tabs: QTabWidget
    filter_edit: QLineEdit
    column_sync_timer: QTimer
    address_completion_model: QStringListModel
    address_completer: QCompleter
    alt_down_shortcut: QShortcut
    ctrl_f_shortcut: QShortcut
    address_completion_timer: QTimer
    tab_groups_coordinator: PanelTabGroupsCoordinator
    _closed_tab_recorder: Callable[[Path], None] | None

    def __init__(
        self,
        panel_id: int,
        default_path: Path,
        show_hidden: bool,
        show_root_dropdown: bool = False,
        show_tab_close_buttons: bool = True,
        roots_provider: Callable[[Path | None], list[Path]] | None = None,
        parent: QWidget | None = None,
        *,
        file_list_size_formatter: Callable[[int], str] | None = None,
        properties_size_formatter: Callable[[int], str] | None = None,
    ) -> None:
        super().__init__(parent)
        self.panel_id = panel_id
        self._show_hidden = show_hidden
        self._show_system_files = True
        self.show_root_dropdown = bool(show_root_dropdown)
        self.default_path = Path(default_path)
        self._roots_provider = roots_provider or list_roots_for_navigation
        self._root_paths: list[Path] = []
        self.column_widths: list[int] = []
        self.syncing_column_widths = False
        self.pending_column_widths_sync: list[int] = []
        self.pending_column_widths_source_tab: ExplorerTab | None = None
        self.restoring_state = False
        self.column_width_auto_align_mode = self.COLUMN_ALIGN_MODE_CURRENT_PANEL_TABS
        self.root_buttons: list[QPushButton] = []
        self.breadcrumb_buttons = []
        self._history_menu: QMenu | None = None
        self._root_picker_menu: QMenu | None = None
        self._closed_tab_recorder = None
        self.pane_role = "normal"
        self._address_completions_enabled = True
        self.active_role_color = QColor("#A8B6C4")
        self.active_role_intensity_percent = 24
        self.target_role_color = QColor("#D2CCAA")
        self.target_role_intensity_percent = 28
        self.show_refresh_button = True
        self.show_root_buttons = True
        self.show_address_bar = True
        self.show_breadcrumb_bar = True
        self.show_navigation_buttons = True
        self.show_history_button = True
        self.show_bookmarks_button = True
        self.show_tab_bar = True
        self.show_tab_close_buttons = bool(show_tab_close_buttons)
        self._append_directory_backslash = False
        self._directories_sort_mode = "like_files"
        self._show_parent_dir_at_drive_root = True
        self._show_square_brackets_around_directories = True
        self._name_sort_method = "natural_locale"
        self._file_icon_mode = "all_associated"
        self._dim_hidden_entries = True
        self._file_icon_size_px = 16
        self._file_icon_padding_horizontal = 2
        self._file_icon_padding_vertical = 1
        self.tab_position_mode = normalize_panel_tab_position_mode(
            self.TAB_POSITION_MODE_DEFAULT
        )
        self.file_list_font_value = QFont(self.font())
        self.navigation_font_value = QFont(self.font())
        self.file_list_size_formatter = (
            file_list_size_formatter or self.default_file_list_size_formatter
        )
        self.properties_size_formatter = (
            properties_size_formatter or self.default_properties_size_formatter
        )
        self.enable_right_click_row_selection = True
        self.keypad_mark_scope = "files_only"
        self.navigation_coordinator = PanelNavigationCoordinator(
            self,
            entry_hidden_system_flags=_entry_hidden_system_flags,
        )
        self.inline_filter_coordinator = PanelInlineFilterCoordinator(self)
        self.presentation_coordinator = PanelPresentationCoordinator(self)
        self.state_coordinator = PanelStateCoordinator(self)
        self.widget_map_coordinator = PanelWidgetMapCoordinator(self)

        self._panel_widget_id = widget_naming.panel_widget_id(self.panel_id)
        assign_widget_identity(
            self,
            widget_id=self._panel_widget_id,
            widget_alias=widget_naming.panel_alias(self.panel_id),
        )
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

        self.focus_watcher = _FocusWatcher(self)
        self.focus_watcher.focused.connect(self.activated)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        build_panel_toolbar(self, root)
        build_panel_tabs(self, root)
        self.tab_groups_coordinator = PanelTabGroupsCoordinator(self)
        build_panel_filter(self)
        assign_panel_control_identities(self)
        install_panel_focus_watchers(self)
        configure_panel_shortcuts_and_timers(self)
        finalize_panel_ui(self)

    @property
    def active_group_id(self) -> str:
        """Return the identifier of the active tab group."""

        return self.tab_groups_coordinator.active_group_id

    @property
    def active_group_title(self) -> str:
        """Return the title of the active tab group."""

        return self.tab_groups_coordinator.active_group_title

    def group_count(self) -> int:
        """Return the number of tab groups owned by this panel."""

        return self.tab_groups_coordinator.group_count()

    def total_tab_count(self) -> int:
        """Return the total number of tabs across all panel groups."""

        return self.tab_groups_coordinator.total_tab_count()

    def ordered_group_choices(
        self,
        *,
        include_active: bool = True,
    ) -> list[tuple[str, str]]:
        """Return ordered `(group_id, title)` pairs for this panel."""

        return self.tab_groups_coordinator.ordered_group_choices(
            include_active=include_active
        )

    def can_close_active_group(self) -> bool:
        """Return whether the active tab group can be closed."""

        return self.tab_groups_coordinator.can_close_active_group()

    def create_group(
        self,
        *,
        title: str | None = None,
        seed_paths: list[Path] | None = None,
        activate: bool = True,
    ) -> str:
        """Create a new tab group and optionally activate it."""

        return self.tab_groups_coordinator.create_group(
            title=title,
            seed_paths=seed_paths,
            activate=activate,
        )

    def rename_group(self, group_id: str, title: str) -> bool:
        """Rename one existing tab group."""

        return self.tab_groups_coordinator.rename_group(group_id, title)

    def close_group(self, group_id: str) -> bool:
        """Close one tab group when more than one group exists."""

        return self.tab_groups_coordinator.close_group(group_id)

    def switch_to_group(self, group_id: str, *, focus_view: bool = False) -> bool:
        """Switch the visible tab strip to the requested group."""

        return self.tab_groups_coordinator.switch_to_group(
            group_id,
            focus_view=focus_view,
        )

    def focus_relative_group(self, step: int) -> bool:
        """Move forward or backward through ordered tab groups."""

        return self.tab_groups_coordinator.focus_relative_group(step)

    def clone_current_tab_to_new_group(self) -> str | None:
        """Create a new group seeded with a copy of the current tab path."""

        return self.tab_groups_coordinator.clone_current_tab_to_new_group()

    def move_current_tab_to_group(self, target_group_id: str) -> bool:
        """Move the current tab into another group and activate that group."""

        return self.tab_groups_coordinator.move_current_tab_to_group(target_group_id)

    def move_current_tab_to_new_group(self) -> str | None:
        """Move the current tab into a newly created tab group."""

        return self.tab_groups_coordinator.move_current_tab_to_new_group()

    def add_tab(self, path: Path) -> ExplorerTab:
        """Add one explorer tab to the active tab group."""

        return self.tab_groups_coordinator.add_tab(path)

    def serialize_tab_groups(self) -> list[TabGroupState]:
        """Serialize all tab groups owned by this panel."""

        return self.tab_groups_coordinator.serialize_tab_groups()

    def sync_active_group_state(self) -> None:
        """Persist the visible tab widget state back into the active group."""

        self.tab_groups_coordinator.sync_active_group_state()

    def restore_tab_groups(
        self,
        groups: list[TabGroupState],
        *,
        active_group_id: str,
    ) -> None:
        """Restore this panel from serialized tab-group state."""

        self.tab_groups_coordinator.restore_tab_groups(
            groups,
            active_group_id=active_group_id,
        )

    def on_group_picker_index_changed(self, index: int) -> None:
        """Switch groups when the toolbar picker changes selection."""

        self.tab_groups_coordinator.on_group_picker_index_changed(index)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Resize and (
            obj is self or self._is_active_files_list_source(obj)
        ):
            self.inline_filter_coordinator.position_overlay()
            return super().eventFilter(obj, event)
        if event.type() == QEvent.Type.MouseButtonDblClick and obj is self.tabs:
            mouse_event = cast("QMouseEvent", event)
            if self._is_tab_strip_blank_double_click(mouse_event):
                self.duplicate_current_tab()
                return True
        if event.type() == QEvent.Type.KeyPress:
            key_event = cast("QKeyEvent", event)
            if obj is self.filter_edit and key_event.key() in {
                int(Qt.Key.Key_Escape),
                int(Qt.Key.Key_Return),
                int(Qt.Key.Key_Enter),
            }:
                if key_event.key() == int(Qt.Key.Key_Escape):
                    self.inline_filter_coordinator.clear()
                self.inline_filter_coordinator.hide_overlay()
                self._focus_current_view()
                return True
            if (
                key_event.modifiers() == Qt.KeyboardModifier.AltModifier
                and key_event.key() == int(Qt.Key.Key_Down)
            ):
                self.navigation_coordinator.show_history_menu()
                return True
            if self._is_active_files_list_source(
                obj
            ) and self.inline_filter_coordinator.should_start_from_key(key_event):
                self.inline_filter_coordinator.show_overlay(seed_text=key_event.text())
                return True
        return super().eventFilter(obj, event)

    def close_current_tab(self) -> None:
        index = self.tabs.currentIndex()
        if index < 0:
            return
        self.state_coordinator.close_tab_at(index)

    def focus_relative_tab(self, step: int) -> bool:
        """Move to a sibling tab inside the active group and focus its file list."""

        count = self.tabs.count()
        if count <= 1:
            return False
        current_index = self.tabs.currentIndex()
        if current_index < 0:
            current_index = 0
        next_index = (current_index + step) % count
        self.tabs.setCurrentIndex(next_index)
        self._focus_current_view()
        return True

    def duplicate_current_tab(self) -> ExplorerTab | None:
        """Duplicate the active tab into a newly selected tab."""

        tab = self.current_tab()
        if tab is None:
            return None
        return self.add_tab(tab.navigation.path)

    def current_path(self) -> Path:
        tab = self.current_tab()
        return tab.navigation.path if tab else self.default_path

    def current_tab(self) -> ExplorerTab | None:
        widget = self.tabs.currentWidget()
        return widget if isinstance(widget, ExplorerTab) else None

    @property
    def navigation_font(self) -> QFont:
        return QFont(self.navigation_font_value)

    @property
    def show_root_dropdown_enabled(self) -> bool:
        return self.show_root_dropdown

    @property
    def show_hidden_enabled(self) -> bool:
        return self._show_hidden

    @property
    def show_system_files_enabled(self) -> bool:
        """Return whether system files are visible in this panel."""

        return self._show_system_files

    @property
    def file_icon_mode(self) -> str:
        """Return the active root and file-list icon mode."""

        return self._file_icon_mode

    @property
    def root_paths(self) -> list[Path]:
        return list(self._root_paths)

    def set_root_paths(self, paths: list[Path]) -> None:
        self._root_paths = [Path(path) for path in paths]

    def provided_roots(self, current_path: Path | None) -> list[Path]:
        return list(self._roots_provider(current_path))

    @property
    def address_completions_enabled(self) -> bool:
        return self._address_completions_enabled

    def set_address_completions_enabled(self, enabled: bool) -> None:
        self._address_completions_enabled = bool(enabled)

    def stop_address_completion_timer(self) -> None:
        self.address_completion_timer.stop()

    def start_address_completion_timer(self, interval_ms: int) -> None:
        self.address_completion_timer.start(int(interval_ms))

    def set_address_completion_suggestions(self, suggestions: list[str]) -> None:
        self.address_completion_model.setStringList([str(item) for item in suggestions])

    def show_address_completion_popup(self) -> None:
        self.address_completer.setCompletionPrefix("")
        self.address_completer.complete(self.address_edit.rect())

    def completion_popup(self) -> QAbstractItemView | None:
        return self.address_completer.popup()

    def take_history_menu(self) -> QMenu | None:
        menu = self._history_menu
        self._history_menu = None
        return menu

    def set_history_menu(self, menu: QMenu | None) -> None:
        self._history_menu = menu

    def take_root_picker_menu(self) -> QMenu | None:
        menu = self._root_picker_menu
        self._root_picker_menu = None
        return menu

    def set_root_picker_menu(self, menu: QMenu | None) -> None:
        self._root_picker_menu = menu

    def tab_count(self) -> int:
        return self.tabs.count()

    def set_show_hidden(self, enabled: bool) -> None:
        self._show_hidden = bool(enabled)
        for tab in self.iter_all_tabs():
            tab.navigation.set_show_hidden(self._show_hidden)
        if self.address_edit.hasFocus():
            self.navigation_coordinator.schedule_address_completion_update(
                self.address_edit.text()
            )
        self.navigation_coordinator.rebuild_breadcrumbs(self.current_path())

    def set_show_system_files(self, enabled: bool) -> None:
        """Toggle system-file visibility and refresh all tabs."""

        self._show_system_files = bool(enabled)
        for tab in self.iter_all_tabs():
            tab.navigation.set_show_system_files(self._show_system_files)
        if self.address_edit.hasFocus():
            self.navigation_coordinator.schedule_address_completion_update(
                self.address_edit.text()
            )

    def set_keypad_mark_scope(self, scope: str) -> None:
        """Apply keypad bulk-mark scope to all tabs in this panel."""

        self.keypad_mark_scope = (
            "files_and_directories"
            if str(scope).strip().lower() == "files_and_directories"
            else "files_only"
        )
        for tab in self.iter_all_tabs():
            tab.set_keypad_mark_scope(self.keypad_mark_scope)

    def set_show_root_dropdown(self, enabled: bool) -> None:
        self.presentation_coordinator.apply_toolbar_visibility(
            show_refresh_button=self.show_refresh_button,
            show_root_buttons=self.show_root_buttons,
            show_root_dropdown=enabled,
            show_address_bar=self.show_address_bar,
            show_breadcrumb_bar=self.show_breadcrumb_bar,
            show_navigation_buttons=self.show_navigation_buttons,
            show_history_button=self.show_history_button,
            show_bookmarks_button=self.show_bookmarks_button,
        )

    def set_directories_sort_mode(self, mode: str) -> None:
        """Apply the configured directory sorting mode to all tabs."""

        self._directories_sort_mode = str(mode).strip().lower() or "like_files"
        for tab in self.iter_all_tabs():
            tab.set_directories_sort_mode(self._directories_sort_mode)

    def set_show_parent_dir_at_drive_root(self, enabled: bool) -> None:
        """Apply drive-root parent-row behavior across all tabs."""

        self._show_parent_dir_at_drive_root = bool(enabled)
        for tab in self.iter_all_tabs():
            tab.set_show_parent_dir_at_drive_root(self._show_parent_dir_at_drive_root)

    def set_show_square_brackets_around_directories(self, enabled: bool) -> None:
        """Apply directory square-bracket formatting across all tabs."""

        self._show_square_brackets_around_directories = bool(enabled)
        for tab in self.iter_all_tabs():
            tab.set_show_square_brackets_around_directories(
                self._show_square_brackets_around_directories
            )

    def set_append_directory_backslash(self, enabled: bool) -> None:
        """Apply directory display formatting across all tabs."""

        self._append_directory_backslash = bool(enabled)
        for tab in self.iter_all_tabs():
            tab.set_append_directory_backslash(self._append_directory_backslash)

    def set_name_sort_method(self, mode: str) -> None:
        """Apply file-name sorting semantics across all tabs."""

        self._name_sort_method = str(mode).strip().lower() or "natural_locale"
        for tab in self.iter_all_tabs():
            tab.set_name_sort_method(self._name_sort_method)

    def set_file_icon_preferences(
        self,
        *,
        icon_mode: str,
        dim_hidden_entries: bool,
        icon_size_px: int,
        padding_horizontal_px: int,
        padding_vertical_px: int,
    ) -> None:
        """Apply file-list icon mode and spacing preferences to all tabs."""

        normalized_mode = str(icon_mode).strip().lower()
        if normalized_mode not in ALLOWED_FILE_ICON_MODES:
            normalized_mode = FILE_ICON_MODE_NONE
        self._file_icon_mode = normalized_mode
        self._dim_hidden_entries = bool(dim_hidden_entries)
        self._file_icon_size_px = max(1, int(icon_size_px))
        self._file_icon_padding_horizontal = max(0, int(padding_horizontal_px))
        self._file_icon_padding_vertical = max(0, int(padding_vertical_px))
        for tab in self.iter_all_tabs():
            tab.set_file_icon_mode(
                self._file_icon_mode,
                dim_hidden_entries=self._dim_hidden_entries,
            )
            tab.set_file_list_icon_metrics(
                icon_size_px=self._file_icon_size_px,
                padding_horizontal_px=self._file_icon_padding_horizontal,
                padding_vertical_px=self._file_icon_padding_vertical,
            )
        self.navigation_coordinator.rebuild_root_controls(self.current_path())

    def resolved_tab_position_mode(self, *, default_tab_position: str) -> str:
        """Return the effective tab-position mode for this panel."""

        return resolve_tab_position_mode(
            self.tab_position_mode,
            default_tab_position=default_tab_position,
        )

    def assign_identity(self, widget: QWidget, widget_id: str, alias: str) -> None:
        assign_widget_identity(widget, widget_id=widget_id, widget_alias=alias)

    def retitle_tab(self, tab: ExplorerTab) -> None:
        index = self.tabs.indexOf(tab)
        if index == -1:
            return
        self.tabs.setTabText(index, _tab_label(tab.navigation.path))

    def default_file_list_size_formatter(self, value: int) -> str:
        return f"{int(value):,}"

    def default_properties_size_formatter(self, value: int) -> str:
        return f"{int(value):,}"

    def handle_address_completion_activated(self, path_text: object) -> None:
        self.navigation_coordinator.on_address_completion_activated(str(path_text))

    def iter_all_tabs(self) -> list[ExplorerTab]:
        """Return all explorer tabs across every tab group."""

        return self.tab_groups_coordinator.iter_all_tabs()

    def build_tab_widget(self, path: Path) -> ExplorerTab:
        """Create one connected explorer tab widget for this panel."""

        return self._build_tab_widget(path)

    def focus_current_view(self) -> None:
        """Focus the visible file list in the current tab when available."""

        self._focus_current_view()

    def _build_tab_widget(self, path: Path) -> ExplorerTab:
        """Create and connect one explorer tab widget for the given path."""

        with trace_span(
            "panel.build_tab_widget",
            "panel",
            args={"panel_id": self.panel_id},
        ):
            tab = ExplorerTab(
                path,
                show_hidden=self._show_hidden,
                show_system_files=self._show_system_files,
                directories_sort_mode=self._directories_sort_mode,
                show_parent_dir_at_drive_root=self._show_parent_dir_at_drive_root,
                show_square_brackets_around_directories=(
                    self._show_square_brackets_around_directories
                ),
                append_directory_backslash=self._append_directory_backslash,
                name_sort_method=self._name_sort_method,
                file_icon_mode=self._file_icon_mode,
                dim_hidden_entries=self._dim_hidden_entries,
                enable_right_click_row_selection=self.enable_right_click_row_selection,
                keypad_mark_scope=self.keypad_mark_scope,
                file_list_size_formatter=self.file_list_size_formatter,
                properties_size_formatter=self.properties_size_formatter,
                parent=self,
            )
            self.widget_map_coordinator.assign_tab_identity(tab)

            def _on_navigation_changed(t: ExplorerTab = tab) -> None:
                self.state_coordinator.on_tab_navigation_changed(t)

            def _on_widths_changed(widths: object, t: ExplorerTab = tab) -> None:
                self.state_coordinator.on_tab_column_widths_changed(t, widths)

            tab.navigation.changed.connect(_on_navigation_changed)
            tab.columns.changed.connect(_on_widths_changed)
            tab.view.setFont(self.file_list_font_value)
            tab.set_file_list_icon_metrics(
                icon_size_px=self._file_icon_size_px,
                padding_horizontal_px=self._file_icon_padding_horizontal,
                padding_vertical_px=self._file_icon_padding_vertical,
            )

            tab.installEventFilter(self.focus_watcher)
            tab.view.installEventFilter(self.focus_watcher)
            tab.installEventFilter(self)
            tab.view.installEventFilter(self)
            return tab

    def set_closed_tab_recorder(
        self,
        recorder: Callable[[Path], None] | None,
    ) -> None:
        """Register the window-level callback used for closed-tab history."""

        self._closed_tab_recorder = recorder

    def record_closed_tab_path(self, path: Path) -> None:
        """Report one closed tab path to the owning window coordinator."""

        if self._closed_tab_recorder is None:
            return
        self._closed_tab_recorder(Path(path))

    def _is_active_files_list_source(self, obj: QObject) -> bool:
        tab = self.current_tab()
        if tab is None:
            return False
        return obj is tab.view

    def _focus_current_view(self) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.view.setFocus()

    def _is_tab_strip_blank_double_click(self, event: QMouseEvent) -> bool:
        """Return whether a double click landed in blank tab-strip space."""

        if event.button() != Qt.MouseButton.LeftButton:
            return False
        tab_bar_rect = self.tabs.tabBar().geometry()
        position = event.position().toPoint()
        if position.y() < tab_bar_rect.top() or position.y() > tab_bar_rect.bottom():
            return False
        return position.x() > tab_bar_rect.right()
