"""Explorer tab widget hosting the file tree and tab navigation state."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import TYPE_CHECKING, cast

from PySide6.QtCore import QEvent, QModelIndex, QObject, QSize, Qt
from PySide6.QtGui import QKeyEvent, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)
from threep_commons.fs_paths import path_key

from ._explorer_tab_actions import ExplorerTabActions
from ._explorer_tab_columns import ExplorerTabColumns
from ._explorer_tab_navigation import ExplorerTabNavigation
from .explorer_file_list_view import ExplorerFileListView
from .fast_dir_model import FastDirModel

if TYPE_CHECKING:
    from collections.abc import Callable

    from .ui.window.state_types import TabState


class ExplorerTab(QWidget):
    """Combine directory model, view, actions, and navigation for one tab."""

    def __init__(
        self,
        initial_path: Path,
        show_hidden: bool = True,
        show_system_files: bool = True,
        directories_sort_mode: str = "like_files",
        show_parent_dir_at_drive_root: bool = True,
        show_square_brackets_around_directories: bool = True,
        append_directory_backslash: bool = False,
        name_sort_method: str = "natural_locale",
        file_icon_mode: str = "all_associated",
        dim_hidden_entries: bool = True,
        enable_right_click_row_selection: bool = True,
        mouse_selection_mode: str | None = None,
        file_list_size_formatter: Callable[[int], str] | None = None,
        properties_size_formatter: Callable[[int], str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tab_uuid = uuid.uuid4().hex
        self._file_list_size_formatter = (
            file_list_size_formatter or self._default_file_list_size_formatter
        )
        self._properties_size_formatter = (
            properties_size_formatter or self._default_properties_size_formatter
        )
        self._pending_mark_restore_paths: list[Path] | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.model = FastDirModel(self)
        self.model.set_size_formatter(self._file_list_size_formatter)
        self.model.set_directories_sort_mode(directories_sort_mode)
        self.model.set_show_parent_dir_at_drive_root(show_parent_dir_at_drive_root)
        self.model.set_show_square_brackets_around_directories(
            show_square_brackets_around_directories
        )
        self.model.set_append_directory_backslash(append_directory_backslash)
        self.model.set_name_sort_method(name_sort_method)
        self.model.set_file_icon_mode(
            file_icon_mode,
            dim_hidden_entries=dim_hidden_entries,
        )
        self.model.setReadOnly(False)

        self.view = ExplorerFileListView()
        self.view.setModel(self.model)
        self.view.setRootIsDecorated(False)
        self.view.setAlternatingRowColors(True)
        self.view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.view.setDragEnabled(True)
        self.view.setAcceptDrops(False)
        self.view.setDropIndicatorShown(False)
        self.view.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.view.setSortingEnabled(True)
        self.view.set_enable_right_click_row_selection(enable_right_click_row_selection)
        self.view.set_mouse_selection_mode(
            mouse_selection_mode
            or ("right_button" if enable_right_click_row_selection else "left_button")
        )
        self.view.installEventFilter(self)
        root.addWidget(self.view)

        self.status_label = QLabel(self)
        self.status_label.setObjectName("explorer_tab_status")
        self.status_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction
        )
        root.addWidget(self.status_label)

        self.columns = ExplorerTabColumns(
            model=self.model,
            view=self.view,
            parent=self,
        )
        self.navigation = ExplorerTabNavigation(
            owner=self,
            model=self.model,
            view=self.view,
            columns=self.columns,
            show_hidden=show_hidden,
            show_system_files=show_system_files,
            parent=self,
        )
        self.navigation.set_show_parent_dir_at_drive_root(show_parent_dir_at_drive_root)
        self._actions = ExplorerTabActions(self, parent=self)

        self.view.customContextMenuRequested.connect(self._actions.open_context_menu)
        self.view.delayed_context_menu_requested.connect(
            self._actions.open_context_menu
        )
        self.view.doubleClicked.connect(self._on_item_activated)
        self.view.activated.connect(self._on_item_activated)
        selection_model = self.view.selectionModel()
        selection_model.selectionChanged.connect(self._on_marks_changed)
        selection_model.currentChanged.connect(self._on_current_index_changed)
        self.model.directory_loaded.connect(self._on_directory_loaded)
        self.model.folder_size_state_changed.connect(self._on_folder_size_changed)
        self.model.modelReset.connect(self.refresh_status_summary)

        self._alt_left_shortcut = QShortcut("Alt+Left", self)
        self._alt_left_shortcut.setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        self._alt_left_shortcut.activated.connect(self.navigation.go_back)

        self._alt_right_shortcut = QShortcut("Alt+Right", self)
        self._alt_right_shortcut.setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        self._alt_right_shortcut.activated.connect(self.navigation.go_forward)

        self._alt_up_shortcut = QShortcut("Alt+Up", self)
        self._alt_up_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._alt_up_shortcut.activated.connect(self.navigation.go_up)

        self.navigation.set_path(initial_path)
        self.view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.refresh_status_summary()

    @property
    def tab_uuid(self) -> str:
        return self._tab_uuid

    @property
    def properties_size_formatter(self) -> Callable[[int], str]:
        return self._properties_size_formatter

    def serialize_state(self) -> TabState:
        return {"path": str(self.navigation.path)}

    def set_file_size_formatter(self, formatter: Callable[[int], str] | None) -> None:
        self._file_list_size_formatter = (
            formatter or self._default_file_list_size_formatter
        )
        self.model.set_size_formatter(self._file_list_size_formatter)

    def set_properties_size_formatter(
        self,
        formatter: Callable[[int], str] | None,
    ) -> None:
        self._properties_size_formatter = (
            formatter or self._default_properties_size_formatter
        )

    def set_enable_right_click_row_selection(self, enabled: bool) -> None:
        """Apply the configured right-button mouse-selection mode."""

        self.view.set_enable_right_click_row_selection(enabled)
        self.view.set_mouse_selection_mode(
            "right_button" if bool(enabled) else "left_button"
        )

    def set_mouse_selection_mode(self, mode: str) -> None:
        """Apply the configured file-list mouse selection mode."""

        self.view.set_mouse_selection_mode(mode)

    def set_directories_sort_mode(self, mode: str) -> None:
        """Apply one directory-sorting mode to the tab model."""

        self.model.set_directories_sort_mode(mode)

    def set_show_parent_dir_at_drive_root(self, enabled: bool) -> None:
        """Apply drive-root parent-row behavior to the tab model and navigation."""

        self.model.set_show_parent_dir_at_drive_root(enabled)
        self.navigation.set_show_parent_dir_at_drive_root(enabled)

    def set_show_square_brackets_around_directories(self, enabled: bool) -> None:
        """Apply directory square-bracket formatting to the tab model."""

        self.model.set_show_square_brackets_around_directories(enabled)

    def set_append_directory_backslash(self, enabled: bool) -> None:
        """Apply directory-name formatting to the tab model."""

        self.model.set_append_directory_backslash(enabled)

    def set_name_sort_method(self, mode: str) -> None:
        """Apply file-name sorting semantics to the tab model."""

        self.model.set_name_sort_method(mode)

    def set_file_icon_mode(self, mode: str, *, dim_hidden_entries: bool) -> None:
        """Apply icon and hidden-entry rendering preferences to the model."""

        self.model.set_file_icon_mode(mode, dim_hidden_entries=dim_hidden_entries)

    def set_file_list_icon_metrics(
        self,
        *,
        icon_size_px: int,
        padding_horizontal_px: int,
        padding_vertical_px: int,
    ) -> None:
        """Apply icon size and row padding to the file-list view."""

        self.view.setIconSize(QSize(int(icon_size_px), int(icon_size_px)))
        self.view.setStyleSheet(
            "QTreeView::item { "
            f"padding-top: {int(padding_vertical_px)}px; "
            f"padding-bottom: {int(padding_vertical_px)}px; "
            f"padding-left: {int(padding_horizontal_px)}px; "
            f"padding-right: {int(padding_horizontal_px)}px; "
            "}"
        )

    def queue_folder_size_calculation(
        self,
        paths: list[Path],
        *,
        announce: bool = False,
    ) -> int:
        """Queue folder-size calculation for paths visible in this tab."""

        return self._actions.queue_folder_size_calculation(paths, announce=announce)

    def selected_paths(self) -> list[Path]:
        """Return the marked operation targets for compatibility callers."""

        return self.marked_paths()

    def marked_paths(self) -> list[Path]:
        """Return the currently marked real filesystem paths."""

        rows = self.view.selectionModel().selectedRows()
        paths: list[Path] = []
        for idx in rows:
            if self.model.is_parent_index(idx):
                continue
            file_path = self.model.filePath(idx)
            if file_path:
                paths.append(Path(file_path))
        return paths

    def marked_or_current_paths(self) -> list[Path]:
        """Return marked paths, or fall back to the current real row."""

        marked = self.marked_paths()
        if marked:
            return marked
        current = self.current_path_or_none()
        return [current] if current is not None else []

    def current_path_or_none(self) -> Path | None:
        """Return the current real row path when available."""

        current_index = self.view.currentIndex().siblingAtColumn(0)
        if not current_index.isValid() or self.model.is_parent_index(current_index):
            return None
        file_path = self.model.filePath(current_index)
        if not file_path:
            return None
        return Path(file_path)

    def clear_marks(self) -> None:
        """Clear all currently marked rows."""

        self.view.selectionModel().clearSelection()

    def is_path_marked(self, path: Path) -> bool:
        """Return whether the given path is currently marked."""

        target_key = path_key(Path(path))
        return any(
            path_key(marked_path) == target_key for marked_path in self.marked_paths()
        )

    def set_path_marked(self, path: Path, marked: bool) -> None:
        """Mark or unmark one visible path if it is currently present."""

        index = self.model.index_for_path(Path(path))
        if not index.isValid():
            return
        flags = (
            self.view.selectionModel().SelectionFlag.Select
            if marked
            else self.view.selectionModel().SelectionFlag.Deselect
        )
        self.view.selectionModel().select(
            index,
            flags | self.view.selectionModel().SelectionFlag.Rows,
        )

    def toggle_mark_at_index(self, index: QModelIndex) -> bool:
        """Toggle one real row mark state and return whether it is now marked."""

        row_index = index.siblingAtColumn(0)
        if not row_index.isValid() or self.model.is_parent_index(row_index):
            return False
        selection_model = self.view.selectionModel()
        selection_model.select(
            row_index,
            selection_model.SelectionFlag.Toggle | selection_model.SelectionFlag.Rows,
        )
        return selection_model.isSelected(row_index)

    def mark_range(self, start: QModelIndex, end: QModelIndex) -> None:
        """Additively mark every real row between two indexes."""

        start_row = start.siblingAtColumn(0)
        end_row = end.siblingAtColumn(0)
        if (
            not start_row.isValid()
            or not end_row.isValid()
            or self.model.is_parent_index(start_row)
            or self.model.is_parent_index(end_row)
        ):
            return
        first_row = min(start_row.row(), end_row.row())
        last_row = max(start_row.row(), end_row.row())
        selection_model = self.view.selectionModel()
        for row in range(first_row, last_row + 1):
            candidate = self.model.index(row, 0, self.view.rootIndex())
            if not candidate.isValid() or self.model.is_parent_index(candidate):
                continue
            selection_model.select(
                candidate,
                selection_model.SelectionFlag.Select
                | selection_model.SelectionFlag.Rows,
            )

    def schedule_mark_restore(self, paths: list[Path]) -> None:
        """Store a mark set that should be restored after the next same-path reload."""

        self._pending_mark_restore_paths = [Path(path) for path in paths]

    def prepare_for_path_change(
        self,
        previous_path: Path | None,
        target_path: Path,
    ) -> None:
        """Prepare current-row and mark state before the model path changes."""

        if previous_path is None:
            self._pending_mark_restore_paths = None
            return
        if path_key(previous_path) == path_key(target_path):
            if self._pending_mark_restore_paths is None:
                self._pending_mark_restore_paths = self.marked_paths()
            return
        self._pending_mark_restore_paths = None
        self.clear_marks()

    def refresh_status_summary(self) -> None:
        """Refresh the per-tab marked-vs-total summary strip."""

        marked_count, marked_bytes, marked_pending = self.model.summary_for_paths(
            self.marked_paths()
        )
        total_count, total_bytes, total_pending = self.model.visible_summary()
        size_summary = (
            f"Size {self.model.format_size_value(marked_bytes)}"
            f"/{self.model.format_size_value(total_bytes)}"
        )
        pending_summary = ""
        if marked_pending > 0 or total_pending > 0:
            pending_summary = f" | Pending {marked_pending}/{total_pending}"
        self.status_label.setText(
            f"Marked {marked_count}/{total_count} | {size_summary}{pending_summary}"
        )

    def open_selected_or_current(self) -> None:
        """Open selected files, or the current row when nothing is selected."""

        self._actions.open_selected_or_current()

    def view_selected_or_current(self) -> None:
        """Open selected files with a dedicated viewer when configured."""

        self._actions.view_selected_or_current()

    def edit_selected_or_current(self) -> None:
        """Edit selected files, or the current row when nothing is selected."""

        self._actions.edit_selected_or_current()

    def create_new_file_and_edit(self) -> None:
        """Create a new file in the active folder and open it in the editor."""

        self._actions.create_new_file_and_edit()

    def create_directory(self) -> None:
        """Create a new folder in the active path."""

        self._actions.create_directory()

    def create_zip_from_selection(self) -> None:
        """Open the archive pack dialog for the current selection."""

        self._actions.create_zip_from_selection()

    def calculate_selected_or_current_folder_sizes(self) -> None:
        """Calculate folder sizes for selected folders or the current folder."""

        self._actions.calculate_selected_or_current_folder_sizes()

    def calculate_visible_folder_sizes(self) -> None:
        """Calculate folder sizes for every visible folder in the active path."""

        self._actions.calculate_visible_folder_sizes()

    def launch_everything_search(self) -> None:
        """Launch Everything scoped to the active tab path."""

        self._actions.launch_everything_search()

    def extract_supported_archive(self) -> None:
        """Open the archive unpack dialog for one selected archive."""

        self._actions.extract_supported_archive()

    def test_supported_archives(self) -> None:
        """Queue or run archive tests for the current archive selection."""

        self._actions.test_supported_archives()

    def open_terminal_here(self) -> None:
        """Open the configured terminal at the active tab path."""

        self._actions.open_terminal_here()

    def copy_selected_item_or_panel_path(self) -> None:
        """Copy a selected item path, or fall back to the active panel path."""

        self._actions.copy_selected_item_or_panel_path()

    def show_properties_selected_or_current(self) -> None:
        """Open properties for the selected item or current row."""

        self._actions.show_properties_selected_or_current()

    def rename_selected_or_current(self) -> None:
        """Rename the selected item or current row."""

        self._actions.rename_selected_or_current()

    def copy_selected_or_current_to_current_directory(self) -> None:
        """Copy the selection into the current directory."""

        self._actions.copy_selected_or_current_to_current_directory()

    def create_directory_in_target(self) -> None:
        """Create one directory in the resolved target pane."""

        self._actions.create_directory_in_target()

    def open_selected_or_current_in_target_pane(self) -> None:
        """Open the selected directory in the resolved target pane."""

        self._actions.open_selected_or_current_in_target_pane()

    def sort_by_column(self, column: int) -> None:
        """Sort the current file list by one column."""

        self._actions.sort_by_column(column)

    def go_root(self) -> None:
        """Jump to the active root or drive root."""

        self._actions.go_root()

    def show_drive_root_parent_picker(self) -> None:
        """Show the panel root picker when `..` is activated at a drive root."""

        owner = self.parentWidget()
        while owner is not None:
            navigation_coordinator = getattr(owner, "navigation_coordinator", None)
            if navigation_coordinator is not None:
                navigation_coordinator.show_root_picker_menu()
                return
            owner = owner.parentWidget()

    def _on_item_activated(self, index: QModelIndex) -> None:
        if self.model.is_parent_index(index):
            self.navigation.go_up()
            return
        file_path = self.model.filePath(index)
        if not file_path:
            return
        self._actions.open_path(Path(file_path))

    def _on_marks_changed(self, *_args: object) -> None:
        self.refresh_status_summary()

    def _on_current_index_changed(self, *_args: object) -> None:
        self.refresh_status_summary()

    def _on_directory_loaded(self, loaded_path: str) -> None:
        current_path_key = path_key(self.navigation.path)
        if path_key(Path(loaded_path)) != current_path_key:
            return
        if self._pending_mark_restore_paths is not None:
            for marked_path in self._pending_mark_restore_paths:
                self.set_path_marked(marked_path, True)
            self._pending_mark_restore_paths = None
        self.refresh_status_summary()

    def _on_folder_size_changed(self, *_args: object) -> None:
        self.refresh_status_summary()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj is self.view and event.type() == QEvent.Type.KeyPress:
            key_event = cast("QKeyEvent", event)
            if self._handle_file_list_shortcut_key(key_event):
                return True
            if self._handle_navigation_key(key_event):
                index = self.view.currentIndex()
                if index.isValid() and key_event.key() == int(Qt.Key.Key_Right):
                    self._on_item_activated(index)
                return True
        return super().eventFilter(obj, event)

    def _handle_file_list_shortcut_key(self, key_event: QKeyEvent) -> bool:
        modifiers = key_event.modifiers()
        key = key_event.key()
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == int(
            Qt.Key.Key_Tab
        ):
            return self._trigger_window_shortcut("next_tab_shortcut")
        if modifiers == (
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
        ) and key in {
            int(Qt.Key.Key_Tab),
            int(Qt.Key.Key_Backtab),
        }:
            return self._trigger_window_shortcut("previous_tab_shortcut")
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == int(
            Qt.Key.Key_PageDown
        ):
            return self._trigger_window_shortcut("next_tab_alias_shortcut")
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == int(
            Qt.Key.Key_PageUp
        ):
            return self._trigger_window_shortcut("previous_tab_alias_shortcut")
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == int(
            Qt.Key.Key_D
        ):
            return self._trigger_window_shortcut("bookmarks_hotlist_shortcut")
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == int(
            Qt.Key.Key_I
        ):
            return self._trigger_window_shortcut("sync_target_panel_path_shortcut")
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == int(
            Qt.Key.Key_U
        ):
            return self._trigger_window_shortcut("exchange_panel_paths_shortcut")
        if modifiers == Qt.KeyboardModifier.NoModifier and key == int(
            Qt.Key.Key_Insert
        ):
            self._actions.toggle_current_item_selection_and_advance()
            return True
        if modifiers == Qt.KeyboardModifier.NoModifier and key == int(Qt.Key.Key_Space):
            self._actions.toggle_current_item_selection()
            return True
        if modifiers == Qt.KeyboardModifier.NoModifier and key == int(Qt.Key.Key_F3):
            return self._trigger_window_shortcut("list_files_shortcut")
        if modifiers == Qt.KeyboardModifier.AltModifier and key == int(Qt.Key.Key_F3):
            return self._trigger_window_shortcut("alt_list_files_shortcut")
        if modifiers == Qt.KeyboardModifier.NoModifier and key == int(Qt.Key.Key_F4):
            return self._trigger_window_shortcut("edit_files_shortcut")
        if modifiers == Qt.KeyboardModifier.ShiftModifier and key == int(Qt.Key.Key_F4):
            return self._trigger_window_shortcut("new_file_shortcut")
        if modifiers == Qt.KeyboardModifier.NoModifier and key == int(Qt.Key.Key_F5):
            return self._trigger_window_action("copy_to_target_action")
        if modifiers == Qt.KeyboardModifier.NoModifier and key == int(Qt.Key.Key_F6):
            return self._trigger_window_action("move_to_target_action")
        if modifiers == Qt.KeyboardModifier.NoModifier and key == int(Qt.Key.Key_F7):
            return self._trigger_window_shortcut("create_directory_shortcut")
        if modifiers == Qt.KeyboardModifier.NoModifier and key == int(Qt.Key.Key_F8):
            return self._trigger_window_action("delete_selection_action")
        if modifiers == Qt.KeyboardModifier.NoModifier and key == int(Qt.Key.Key_F9):
            return self._trigger_window_shortcut("terminal_here_shortcut")
        if modifiers == Qt.KeyboardModifier.AltModifier and key == int(Qt.Key.Key_F7):
            self.launch_everything_search()
            return True
        if modifiers == Qt.KeyboardModifier.AltModifier and key == int(Qt.Key.Key_F9):
            self.extract_supported_archive()
            return True
        if modifiers == (
            Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ShiftModifier
        ) and key == int(Qt.Key.Key_F9):
            self.test_supported_archives()
            return True
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == int(
            Qt.Key.Key_L
        ):
            self.calculate_selected_or_current_folder_sizes()
            return True
        if modifiers == (
            Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ShiftModifier
        ) and key in {
            int(Qt.Key.Key_Return),
            int(Qt.Key.Key_Enter),
        }:
            self.calculate_visible_folder_sizes()
            return True
        if modifiers == Qt.KeyboardModifier.AltModifier and key in {
            int(Qt.Key.Key_Return),
            int(Qt.Key.Key_Enter),
        }:
            self.show_properties_selected_or_current()
            return True
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == int(
            Qt.Key.Key_F3
        ):
            self.sort_by_column(0)
            return True
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == int(
            Qt.Key.Key_F4
        ):
            self.sort_by_column(1)
            return True
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == int(
            Qt.Key.Key_F5
        ):
            self.sort_by_column(3)
            return True
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == int(
            Qt.Key.Key_F6
        ):
            self.sort_by_column(2)
            return True
        if modifiers == Qt.KeyboardModifier.ShiftModifier and key == int(Qt.Key.Key_F5):
            self.copy_selected_or_current_to_current_directory()
            return True
        if modifiers == Qt.KeyboardModifier.ShiftModifier and key == int(Qt.Key.Key_F6):
            self.rename_selected_or_current()
            return True
        if modifiers == Qt.KeyboardModifier.ShiftModifier and key == int(Qt.Key.Key_F7):
            self.create_directory_in_target()
            return True
        if modifiers == Qt.KeyboardModifier.NoModifier and key == int(
            Qt.Key.Key_Delete
        ):
            return self._trigger_window_action("delete_selection_action")
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == int(
            Qt.Key.Key_A
        ):
            self._actions.select_all_items()
            return True
        if modifiers == Qt.KeyboardModifier.ShiftModifier and key == int(
            Qt.Key.Key_F10
        ):
            self._actions.open_context_menu_from_keyboard()
            return True
        return False

    def _handle_navigation_key(self, key_event: QKeyEvent) -> bool:
        modifiers = key_event.modifiers()
        key = key_event.key()
        dispatch: dict[tuple[Qt.KeyboardModifier, int], Callable[[], None]] = {
            (
                Qt.KeyboardModifier.AltModifier,
                int(Qt.Key.Key_Left),
            ): self.navigation.go_back,
            (
                Qt.KeyboardModifier.AltModifier,
                int(Qt.Key.Key_Right),
            ): self.navigation.go_forward,
            (
                Qt.KeyboardModifier.AltModifier,
                int(Qt.Key.Key_Up),
            ): self.navigation.go_up,
            (
                Qt.KeyboardModifier.NoModifier,
                int(Qt.Key.Key_Left),
            ): self.navigation.go_up,
            (
                Qt.KeyboardModifier.NoModifier,
                int(Qt.Key.Key_Backspace),
            ): self.navigation.go_up,
        }
        if modifiers == Qt.KeyboardModifier.ControlModifier and key in {
            int(Qt.Key.Key_Backslash),
        }:
            self.go_root()
            return True
        if modifiers in {
            Qt.KeyboardModifier.ControlModifier,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
        } and key == int(Qt.Key.Key_Less):
            self.go_root()
            return True
        if modifiers == Qt.KeyboardModifier.ControlModifier and key in {
            int(Qt.Key.Key_Left),
            int(Qt.Key.Key_Right),
        }:
            self.open_selected_or_current_in_target_pane()
            return True
        handler = dispatch.get((modifiers, key))
        if handler is not None:
            handler()
            return True
        return modifiers == Qt.KeyboardModifier.NoModifier and key == int(
            Qt.Key.Key_Right
        )

    def _trigger_window_action(self, action_name: str) -> bool:
        window = self.window()
        if not isinstance(window, QMainWindow):
            return False
        action = getattr(window, action_name, None)
        if action is None:
            return False
        action.trigger()
        return True

    def _trigger_window_shortcut(self, shortcut_name: str) -> bool:
        """Trigger one window-owned shortcut by attribute name."""

        window = self.window()
        if not isinstance(window, QMainWindow):
            return False
        shortcut = getattr(window, shortcut_name, None)
        if not isinstance(shortcut, QShortcut):
            return False
        shortcut.activated.emit()
        return True

    def _default_file_list_size_formatter(self, value: int) -> str:
        return f"{int(value):,}"

    def _default_properties_size_formatter(self, value: int) -> str:
        return f"{int(value):,}"
