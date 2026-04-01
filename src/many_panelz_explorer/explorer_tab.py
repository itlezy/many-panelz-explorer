"""Explorer tab widget hosting the file tree and tab navigation state."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import TYPE_CHECKING, cast

from PySide6.QtCore import QEvent, QModelIndex, QObject, Qt
from PySide6.QtGui import QKeyEvent, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

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
        enable_right_click_row_selection: bool = True,
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

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.model = FastDirModel(self)
        self.model.set_size_formatter(self._file_list_size_formatter)
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
        self.view.installEventFilter(self)
        root.addWidget(self.view)

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
            parent=self,
        )
        self._actions = ExplorerTabActions(self, parent=self)

        self.view.customContextMenuRequested.connect(self._actions.open_context_menu)
        self.view.delayed_context_menu_requested.connect(self._actions.open_context_menu)
        self.view.doubleClicked.connect(self._on_item_activated)
        self.view.activated.connect(self._on_item_activated)

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
        """Apply the configured delayed right-click row-selection behavior."""

        self.view.set_enable_right_click_row_selection(enabled)

    def queue_folder_size_calculation(
        self,
        paths: list[Path],
        *,
        announce: bool = False,
    ) -> int:
        """Queue folder-size calculation for paths visible in this tab."""

        return self._actions.queue_folder_size_calculation(paths, announce=announce)

    def selected_paths(self) -> list[Path]:
        rows = self.view.selectionModel().selectedRows()
        paths: list[Path] = []
        for idx in rows:
            if self.model.is_parent_index(idx):
                continue
            file_path = self.model.filePath(idx)
            if file_path:
                paths.append(Path(file_path))
        return paths

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

    def _on_item_activated(self, index: QModelIndex) -> None:
        file_path = self.model.filePath(index)
        if not file_path:
            return
        self._actions.open_path(Path(file_path))

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
        if modifiers == Qt.KeyboardModifier.NoModifier and key == int(
            Qt.Key.Key_Space
        ):
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
        if modifiers == Qt.KeyboardModifier.ShiftModifier and key == int(
            Qt.Key.Key_F5
        ):
            self.copy_selected_or_current_to_current_directory()
            return True
        if modifiers == Qt.KeyboardModifier.ShiftModifier and key == int(
            Qt.Key.Key_F6
        ):
            self.rename_selected_or_current()
            return True
        if modifiers == Qt.KeyboardModifier.ShiftModifier and key == int(
            Qt.Key.Key_F7
        ):
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
        if (
            modifiers
            in {
                Qt.KeyboardModifier.ControlModifier,
                Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
            }
            and key == int(Qt.Key.Key_Less)
        ):
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
