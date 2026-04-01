"""Context-menu and file action helpers for a single explorer tab."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QItemSelectionModel, QModelIndex, QObject, QPoint, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
)

from . import external_tools, file_ops
from .dialogs.properties_dialog import PropertiesDialog
from .terminal_launchers import available_terminal_launchers

if TYPE_CHECKING:
    from collections.abc import Callable

    from ._operations.types import TerminalLauncherId
    from ._settings.manager import SettingsManager
    from .explorer_tab import ExplorerTab
    from .panel_widget import PanelWidget
    from .ui.window import WindowBookmarksCoordinator
    from .ui.window.operations import WindowOperationsCoordinator


class ExplorerTabActions(QObject):
    """Own context-menu actions and file operations for an explorer tab."""

    def __init__(self, tab: ExplorerTab, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tab = tab

    def open_context_menu(self, pos: QPoint) -> None:
        menu = QMenu(self._tab)
        menu.setToolTipsVisible(True)
        for text, handler in self._menu_specs():
            if text is None:
                menu.addSeparator()
                continue
            action = QAction(text, self._tab)
            action.triggered.connect(handler)
            menu.addAction(action)
        self._add_bookmark_menu_items(menu)
        self._add_terminal_menu_items(menu)
        menu.exec(self._tab.view.viewport().mapToGlobal(pos))

    def open_context_menu_from_keyboard(self) -> None:
        """Open the file-list context menu near the current row."""

        current_index = self._tab.view.currentIndex()
        current_rect = self._tab.view.visualRect(current_index)
        if current_index.isValid() and current_rect.isValid():
            self.open_context_menu(current_rect.center())
            return
        self.open_context_menu(self._tab.view.viewport().rect().center())

    def open_path(self, path: Path) -> None:
        target = Path(path)
        if target.is_dir():
            self._tab.navigation.set_path(target)
            return
        self._run_action(lambda: file_ops.open_with_default(target))

    def open_selected_or_current(self) -> None:
        """Open selected files, or the current row when nothing is selected."""

        targets = self._selected_or_current_paths()
        if not targets:
            return
        files = [path for path in targets if path.is_file()]
        directories = [path for path in targets if path.is_dir()]
        if files:

            def _open_files() -> None:
                for path in files:
                    file_ops.open_with_default(path)

            self._run_action(_open_files)
            return
        if len(directories) == 1:
            self._tab.navigation.set_path(directories[0])

    def view_selected_or_current(self) -> None:
        """Open selected files in a dedicated viewer when configured."""

        targets = self._selected_or_current_paths()
        if not targets:
            return
        files = [path for path in targets if path.is_file()]
        directories = [path for path in targets if path.is_dir()]
        if files:
            fallback_used = False

            def _open_targets() -> None:
                nonlocal fallback_used
                for path in files:
                    if not file_ops.open_with_viewer(path):
                        fallback_used = True
                        file_ops.open_with_default(path)

            self._run_action(_open_targets)
            if fallback_used:
                self._show_status_message(
                    "No dedicated viewer configured; used default opener.",
                    2200,
                )
            return
        if len(directories) == 1:
            self._tab.navigation.set_path(directories[0])

    def edit_selected_or_current(self) -> None:
        """Edit selected files, or the current file when nothing is selected."""

        files = [path for path in self._selected_or_current_paths() if path.is_file()]
        if not files:
            return

        def _open_files() -> None:
            for path in files:
                file_ops.open_in_text_editor(path)

        self._run_action(_open_files)

    def create_new_file_and_edit(self) -> None:
        """Prompt for a new file name, create it, and open it in the editor."""

        name, ok = QInputDialog.getText(
            self._tab,
            "New file",
            "File name:",
            text="New File.txt",
        )
        if not ok or not name.strip():
            return

        def _create_and_open() -> None:
            created = file_ops.create_text_file(self._tab.navigation.path, name.strip())
            self._tab.navigation.set_path(
                self._tab.navigation.path,
                push_history=False,
                selection_hint=created,
            )
            file_ops.open_in_text_editor(created)

        self._run_action(_create_and_open)

    def copy_selected_item_or_panel_path(self) -> None:
        """Copy a selected path, or fall back to the active panel path."""

        selected = self._selected_real_paths()
        if len(selected) == 1:
            self._copy_text_to_clipboard(str(selected[0]))
            return
        self._copy_text_to_clipboard(str(self._tab.navigation.path))
        self._show_status_message("Copied panel path to clipboard.", 1800)

    def select_all_items(self) -> None:
        """Select all real filesystem rows in the current file list."""

        selection_model = self._tab.view.selectionModel()
        selection_model.clearSelection()
        root_index = self._tab.view.rootIndex()
        flags = (
            QItemSelectionModel.SelectionFlag.Select
            | QItemSelectionModel.SelectionFlag.Rows
        )
        for row in range(self._tab.model.rowCount(root_index)):
            index = self._tab.model.index(row, 0, root_index)
            if not index.isValid() or self._tab.model.is_parent_index(index):
                continue
            selection_model.select(index, flags)
        last_index = self._tab.view.currentIndex()
        if last_index.isValid() and not self._tab.model.is_parent_index(last_index):
            selection_model.setCurrentIndex(last_index, flags)

    def toggle_current_item_selection(self) -> None:
        """Toggle selection on the current real row without changing focus."""

        current_index = self._current_real_index()
        if not current_index.isValid():
            return
        self._toggle_row_selection(current_index)
        self._tab.view.scrollTo(
            current_index,
            QAbstractItemView.ScrollHint.PositionAtCenter,
        )

    def toggle_current_item_selection_and_advance(self) -> None:
        """Toggle selection on the current real row and advance to the next row."""

        current_index = self._current_real_index()
        if not current_index.isValid():
            return
        next_index = self._next_selectable_row_index(current_index)
        self._toggle_row_selection(current_index)
        if not next_index.isValid():
            self._tab.view.scrollTo(
                current_index,
                QAbstractItemView.ScrollHint.PositionAtCenter,
            )
            return
        self._tab.view.selectionModel().setCurrentIndex(
            next_index,
            QItemSelectionModel.SelectionFlag.Current,
        )
        self._tab.view.scrollTo(
            next_index,
            QAbstractItemView.ScrollHint.PositionAtCenter,
        )

    def create_directory(self) -> None:
        """Prompt for and create a new directory in the current path."""

        self._new_folder()

    def create_zip_from_selection(self) -> None:
        """Launch the archive pack dialog for the current selection."""

        self._zip_create()

    def open_terminal_here(self) -> None:
        """Open the configured terminal at the current tab path."""

        self._open_terminal()

    def launch_everything_search(self) -> None:
        """Launch Everything scoped to the active tab path."""

        settings = self._window_settings()
        if settings is None:
            return
        self._run_external_tool_action(
            lambda: external_tools.launch_everything_search(
                executable=settings.everything_executable,
                path=self._tab.navigation.path,
            ),
            timeout_ms=2600,
        )

    def extract_supported_archive(self) -> None:
        """Open the archive unpack dialog for one selected `.7z` or `.rar` file."""

        archive = self._single_selected_or_current_path()
        if archive is None or not archive.is_file():
            return
        suffix = archive.suffix.casefold()
        if suffix not in {".7z", ".rar"}:
            self._show_status_message(
                "Alt+F9 supports only .7z and .rar archives.",
                2400,
            )
            return
        operations = self._window_operations_coordinator()
        if operations is None:
            return
        operations.unpack_archive(archive=archive)

    def show_properties_selected_or_current(self) -> None:
        """Open properties for the selected item or current row."""

        path = self._single_selected_or_current_path()
        if path is None:
            return
        dialog = PropertiesDialog(
            path,
            self._tab,
            size_formatter=self._tab.properties_size_formatter,
        )
        dialog.exec()

    def rename_selected_or_current(self) -> None:
        """Rename the selected item or current row in place."""

        source = self._single_selected_or_current_path()
        if source is None:
            return
        name, ok = QInputDialog.getText(
            self._tab,
            "Rename",
            "New name:",
            text=source.name,
        )
        if not ok or not name.strip():
            return

        def _rename() -> None:
            renamed = file_ops.rename_path(source, name.strip())
            self._tab.navigation.set_path(
                self._tab.navigation.path,
                push_history=False,
                selection_hint=renamed,
            )

        self._run_and_refresh(_rename)

    def copy_selected_or_current_to_current_directory(self) -> None:
        """Copy the selection into the current directory with rename-on-conflict."""

        selected = self._selected_or_current_paths()
        if not selected:
            return

        def _copy() -> None:
            copied = file_ops.copy_items(selected, self._tab.navigation.path)
            selection_hint = copied[0] if len(copied) == 1 else None
            self._tab.navigation.set_path(
                self._tab.navigation.path,
                push_history=False,
                selection_hint=selection_hint,
            )

        self._run_and_refresh(_copy)

    def create_directory_in_target(self) -> None:
        """Create one directory inside the resolved target pane."""

        target_panel = self._target_panel()
        if target_panel is None:
            self._show_status_message(
                "No target pane is available. Create another pane first.",
                2400,
            )
            return
        suggested_name = "New Folder"
        selected = self._single_selected_or_current_path()
        if selected is not None:
            suggested_name = selected.name or suggested_name
        name, ok = QInputDialog.getText(
            self._tab,
            "New folder in target pane",
            "Folder name:",
            text=suggested_name,
        )
        if not ok or not name.strip():
            return

        def _create() -> None:
            created = file_ops.create_folder(target_panel.current_path(), name.strip())
            current_target_tab = target_panel.current_tab()
            if current_target_tab is not None:
                current_target_tab.navigation.set_path(
                    target_panel.current_path(),
                    push_history=False,
                    selection_hint=created,
                )

        self._run_action(_create)
        target_panel.navigation_coordinator.refresh_current_path()

    def open_selected_or_current_in_target_pane(self) -> None:
        """Open the selected directory in the target pane or mirror the current path."""

        target_panel = self._target_panel()
        if target_panel is None:
            self._show_status_message(
                "No target pane is available. Create another pane first.",
                2400,
            )
            return
        candidate = self._single_selected_or_current_path()
        target_path = (
            candidate
            if candidate is not None and candidate.is_dir()
            else self._tab.navigation.path
        )
        current_target_tab = target_panel.current_tab()
        if current_target_tab is None:
            return
        current_target_tab.navigation.set_path(target_path)

    def sort_by_column(self, column: int) -> None:
        """Sort the current file list by one model column in ascending order."""

        self._tab.view.sortByColumn(int(column), Qt.SortOrder.AscendingOrder)

    def go_root(self) -> None:
        """Jump the active panel to its root path."""

        panel = self._active_panel()
        if panel is None:
            return
        panel.navigation_coordinator.go_root()

    def _menu_specs(self) -> list[tuple[str | None, Callable[[], None]]]:
        return [
            ("Open", self._open_selected),
            ("Rename", self._rename_selected),
            ("New folder", self._new_folder),
            (None, self._open_selected),
            ("Copy", self._copy_selected),
            ("Cut", self._cut_selected),
            ("Paste", self._paste_into_current),
            ("Move...", self._move_selected),
            ("Delete", self._delete_selected),
            (None, self._open_selected),
            ("Properties", self._show_properties),
            ("Pack Files...", self._zip_create),
            ("Unpack Files...", self._zip_extract),
        ]

    def _add_terminal_menu_items(self, menu: QMenu) -> None:
        """Append the shared terminal actions to one explorer-tab menu."""

        default_action = QAction("Open terminal here", self._tab)
        default_action.triggered.connect(self._open_terminal)
        menu.addAction(default_action)

        submenu = menu.addMenu("Open terminal with")
        submenu.setToolTipsVisible(True)
        for launcher in available_terminal_launchers():
            action = submenu.addAction(launcher.label)
            if launcher.is_available:
                action.triggered.connect(
                    self._open_terminal_with_callback(launcher.launcher_id)
                )
                continue
            hint = launcher.error or "Configured executable is unavailable."
            action.setEnabled(False)
            action.setToolTip(hint)
            action.setStatusTip(hint)

    def _add_bookmark_menu_items(self, menu: QMenu) -> None:
        """Append quick bookmark actions for the current folder."""

        coordinator = self._window_bookmarks_coordinator()
        if coordinator is None:
            return

        menu.addSeparator()
        add_action = QAction("Add current folder to bookmarks", self._tab)
        add_action.triggered.connect(coordinator.prompt_add_current_folder)
        menu.addAction(add_action)

        remove_action = QAction("Remove current folder bookmark", self._tab)
        remove_action.triggered.connect(coordinator.remove_current_folder)
        remove_action.setEnabled(coordinator.has_current_folder_bookmark())
        menu.addAction(remove_action)

    def _open_selected(self) -> None:
        for path in self._tab.selected_paths():
            if path.is_dir():
                self._tab.navigation.set_path(path)
                continue
            self._run_action(lambda p=path: file_ops.open_with_default(p))

    def _rename_selected(self) -> None:
        self.rename_selected_or_current()

    def _new_folder(self) -> None:
        name, ok = QInputDialog.getText(
            self._tab,
            "New folder",
            "Folder name:",
            text="New Folder",
        )
        if not ok or not name.strip():
            return
        self._run_and_refresh(
            lambda: file_ops.create_folder(self._tab.navigation.path, name.strip())
        )

    def _copy_selected(self) -> None:
        selected = self._tab.selected_paths()
        if selected:
            file_ops.set_clipboard(selected, cut=False)

    def _cut_selected(self) -> None:
        selected = self._tab.selected_paths()
        if selected:
            file_ops.set_clipboard(selected, cut=True)

    def _paste_into_current(self) -> None:
        self._run_and_refresh(lambda: file_ops.paste_items(self._tab.navigation.path))

    def _move_selected(self) -> None:
        selected = self._tab.selected_paths()
        if not selected:
            return
        dest = QFileDialog.getExistingDirectory(
            self._tab,
            "Move items",
            str(self._tab.navigation.path),
        )
        if not dest:
            return
        self._run_and_refresh(lambda: file_ops.move_items(selected, Path(dest)))

    def _delete_selected(self) -> None:
        selected = self._tab.selected_paths()
        if not selected:
            return
        names = "\n".join(path.name for path in selected[:10])
        confirm = QMessageBox.question(
            self._tab,
            "Delete to Recycle Bin",
            f"Move selected items to Recycle Bin?\n\n{names}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self._run_and_refresh(lambda: file_ops.delete_to_recycle_bin(selected))

    def _show_properties(self) -> None:
        self.show_properties_selected_or_current()

    def _zip_create(self) -> None:
        selected = self._selected_or_current_paths()
        if not selected:
            return
        operations = self._window_operations_coordinator()
        if operations is None:
            return
        operations.pack_sources(sources=selected)

    def _zip_extract(self) -> None:
        self.extract_supported_archive()

    def _open_terminal(self) -> None:
        self._run_action(lambda: file_ops.open_terminal_here(self._tab.navigation.path))

    def _open_terminal_with(self, launcher_id: TerminalLauncherId) -> None:
        """Open the current folder with one explicit launcher choice."""

        self._run_action(
            lambda: file_ops.open_terminal_here(
                self._tab.navigation.path,
                launcher_id=launcher_id,
            )
        )

    def _open_terminal_with_callback(
        self,
        launcher_id: TerminalLauncherId,
    ) -> Callable[[bool], None]:
        """Build a callback for an explicit explorer-tab terminal launcher."""

        def _trigger(_checked: bool = False) -> None:
            self._open_terminal_with(launcher_id)

        return _trigger

    def _selected_real_paths(self) -> list[Path]:
        selected: list[Path] = []
        selection_model = self._tab.view.selectionModel()
        for index in selection_model.selectedRows():
            if not index.isValid() or self._tab.model.is_parent_index(index):
                continue
            file_path = self._tab.model.filePath(index)
            if file_path:
                selected.append(Path(file_path))
        return selected

    def _selected_or_current_paths(self) -> list[Path]:
        selected = self._selected_real_paths()
        if selected:
            return selected
        current_index = self._tab.view.currentIndex()
        if not current_index.isValid() or self._tab.model.is_parent_index(
            current_index
        ):
            return []
        file_path = self._tab.model.filePath(current_index)
        if not file_path:
            return []
        return [Path(file_path)]

    def _single_selected_or_current_path(self) -> Path | None:
        paths = self._selected_or_current_paths()
        if len(paths) != 1:
            return None
        return paths[0]

    def _current_real_index(self) -> QModelIndex:
        current_index = self._tab.view.currentIndex()
        if current_index.isValid():
            current_index = current_index.siblingAtColumn(0)
        if not current_index.isValid() or self._tab.model.is_parent_index(
            current_index
        ):
            return QModelIndex()
        return current_index

    def _toggle_row_selection(self, index: QModelIndex) -> None:
        self._tab.view.selectionModel().select(
            index,
            QItemSelectionModel.SelectionFlag.Toggle
            | QItemSelectionModel.SelectionFlag.Rows,
        )

    def _next_selectable_row_index(self, current_index: QModelIndex) -> QModelIndex:
        root_index = self._tab.view.rootIndex()
        row_count = self._tab.model.rowCount(root_index)
        for row in range(current_index.row() + 1, row_count):
            candidate = self._tab.model.index(row, 0, root_index)
            if not candidate.isValid() or self._tab.model.is_parent_index(candidate):
                continue
            return candidate
        return QModelIndex()

    def _copy_text_to_clipboard(self, value: str) -> None:
        clipboard = QApplication.clipboard()
        clipboard.setText(str(value or ""))

    def _show_status_message(self, message: str, timeout_ms: int) -> None:
        window = self._tab.window()
        if isinstance(window, QMainWindow):
            window.statusBar().showMessage(message, timeout_ms)

    def _window_bookmarks_coordinator(self) -> WindowBookmarksCoordinator | None:
        """Return the owning window bookmarks coordinator when available."""

        from .ui.window.bookmarks import WindowBookmarksCoordinator

        window = self._tab.window()
        coordinator = getattr(window, "bookmarks_coordinator", None)
        if not isinstance(coordinator, WindowBookmarksCoordinator):
            return None
        return coordinator

    def _window_settings(self) -> SettingsManager | None:
        """Return the owning window settings when available."""

        from .window import ExplorerWindow

        window = self._tab.window()
        if not isinstance(window, ExplorerWindow):
            return None
        return window.settings

    def _window_operations_coordinator(self) -> WindowOperationsCoordinator | None:
        """Return the owning window operations coordinator when available."""

        from .window import ExplorerWindow

        window = self._tab.window()
        if not isinstance(window, ExplorerWindow):
            return None
        return window.operations_coordinator

    def _active_panel(self) -> PanelWidget | None:
        """Return the active panel when this tab belongs to it."""

        from .window import ExplorerWindow

        window = self._tab.window()
        if not isinstance(window, ExplorerWindow):
            return None
        panel = window.panels_coordinator.active_panel()
        if panel is None or panel.current_tab() is not self._tab:
            return None
        return panel

    def _target_panel(self) -> PanelWidget | None:
        """Return the resolved target panel for this tab."""

        active_panel = self._active_panel()
        if active_panel is None:
            return None
        from .window import ExplorerWindow

        window = self._tab.window()
        if not isinstance(window, ExplorerWindow):
            return None
        target_panel = window.panels_coordinator.target_panel()
        if target_panel is active_panel:
            return None
        return target_panel

    def _run_and_refresh(self, action: Callable[[], object]) -> None:
        self._run_action(action)
        self._tab.navigation.refresh()

    def _run_external_tool_action(
        self,
        action: Callable[[], object],
        *,
        timeout_ms: int,
    ) -> None:
        """Run one optional external-tool action with non-blocking errors."""

        try:
            action()
        except RuntimeError as exc:
            self._show_status_message(str(exc), timeout_ms)
        except Exception as exc:  # pragma: no cover - UI error path
            QMessageBox.critical(self._tab, "Operation failed", str(exc))

    def _run_action(self, action: Callable[[], object]) -> None:
        try:
            action()
        except Exception as exc:  # pragma: no cover - UI error path
            QMessageBox.critical(self._tab, "Operation failed", str(exc))
