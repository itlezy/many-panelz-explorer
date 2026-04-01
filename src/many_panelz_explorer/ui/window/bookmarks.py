"""Bookmarks coordination for one explorer window."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QFileSystemWatcher, QObject, Qt
from PySide6.QtWidgets import QApplication, QInputDialog, QMenu
from threep_commons.desktop import open_path_in_default_app
from threep_commons.fs_paths import display_path_text, path_key

from ... import file_ops
from ...bookmarks import (
    Bookmark,
    BookmarkCollection,
    BookmarkFolderNode,
    BookmarkStore,
    build_bookmark_tree,
    collect_folder_paths,
    default_bookmark_label,
    normalize_bookmark_folder_path,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from ...window import ExplorerWindow


class WindowBookmarksCoordinator(QObject):
    """Own menu-driven bookmark actions for one explorer window."""

    ROOT_FOLDER_LABEL = "<Root>"
    CREATE_FOLDER_LABEL = "<Create new folder...>"

    def __init__(self, window: ExplorerWindow) -> None:
        super().__init__(window)
        self.window = window
        self._store = BookmarkStore.from_settings(window.settings)
        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_bookmarks_fs_changed)
        self._watcher.directoryChanged.connect(self._on_bookmarks_fs_changed)
        self._collection = BookmarkCollection()
        self._tree = BookmarkFolderNode(path="")
        self._reload_bookmarks(report_errors=False)

    @property
    def bookmarks(self) -> tuple[Bookmark, ...]:
        """Return the currently loaded bookmark snapshot."""

        return self._collection.bookmarks

    @property
    def folder_paths(self) -> tuple[str, ...]:
        """Return all known logical bookmark-folder paths."""

        return collect_folder_paths(self._collection)

    @property
    def bookmarks_file(self) -> Path:
        """Return the editable bookmarks TOML path."""

        return self._store.bookmarks_file

    def populate_bookmarks_menu(self, menu: QMenu) -> None:
        """Populate the File > Bookmarks submenu for the current window state."""

        menu.clear()
        menu.addAction(self.window.add_current_folder_bookmark_action)
        self.window.remove_current_folder_bookmark_action.setEnabled(
            self._current_bookmark() is not None
        )
        menu.addAction(self.window.remove_current_folder_bookmark_action)
        menu.addAction(self.window.create_bookmark_folder_action)
        menu.addAction(self.window.edit_bookmarks_file_action)
        menu.addSeparator()

        if not self._tree.folders and not self._tree.bookmarks:
            empty_action = menu.addAction("(No bookmarks)")
            empty_action.setEnabled(False)
            return

        self._populate_folder_menu(menu, self._tree)

    def prompt_add_current_folder(self) -> None:
        """Prompt for a label and destination folder, then add the active folder."""

        current_path = self._current_bookmark_path()
        if current_path is None:
            return
        existing = self._bookmark_for_path(current_path)
        dialog_title = "Update Bookmark" if existing is not None else "Add Bookmark"
        initial_label = (
            existing.label
            if existing is not None
            else default_bookmark_label(current_path)
        )
        label, accepted = QInputDialog.getText(
            self.window,
            dialog_title,
            "Bookmark label:",
            text=initial_label,
        )
        normalized_label = str(label).strip()
        if not accepted or not normalized_label:
            return

        initial_folder = existing.folder if existing is not None else ""
        destination_folder = self._prompt_folder_destination(
            title=dialog_title,
            initial_folder=initial_folder,
        )
        if destination_folder is None:
            return
        if destination_folder:
            self._collection = self._store.create_folder(destination_folder)
        self._collection = self._store.add_or_update(
            path=current_path,
            label=normalized_label,
            folder=destination_folder,
        )
        self._tree = build_bookmark_tree(self._collection)
        self._refresh_watch_paths()
        self._show_status_message("Bookmark saved.", 1800)

    def remove_current_folder(self) -> None:
        """Remove the bookmark for the active folder when present."""

        current_path = self._current_bookmark_path()
        if current_path is None:
            return
        if self._bookmark_for_path(current_path) is None:
            return
        self._collection = self._store.remove(path=current_path)
        self._tree = build_bookmark_tree(self._collection)
        self._refresh_watch_paths()
        self._show_status_message("Bookmark removed.", 1800)

    def create_bookmark_folder(self) -> None:
        """Prompt for and create one logical bookmark folder path."""

        folder_path, accepted = QInputDialog.getText(
            self.window,
            "Create Bookmark Folder",
            "Folder path:",
        )
        if not accepted:
            return
        normalized = normalize_bookmark_folder_path(folder_path)
        if not normalized:
            return
        self._collection = self._store.create_folder(normalized)
        self._tree = build_bookmark_tree(self._collection)
        self._refresh_watch_paths()
        self._show_status_message("Bookmark folder created.", 1800)

    def edit_bookmarks_file(self) -> None:
        """Create and open the editable bookmarks TOML file."""

        bookmarks_file = self._store.ensure_file_exists()
        self._refresh_watch_paths()
        if open_path_in_default_app(bookmarks_file):
            return
        file_ops.open_in_text_editor(bookmarks_file)

    def open_bookmark(self, bookmark: Bookmark) -> None:
        """Open one bookmark using the active keyboard modifiers."""

        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            self._open_bookmark_in_new_window(bookmark.path)
            return
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            self._open_bookmark_in_new_tab(bookmark.path)
            return
        self._open_bookmark_in_active_tab(bookmark.path)

    def has_current_folder_bookmark(self) -> bool:
        """Return whether the active folder currently has a bookmark."""

        return self._current_bookmark() is not None

    def _populate_folder_menu(self, menu: QMenu, node: BookmarkFolderNode) -> None:
        """Populate one menu level from a tree node."""

        for folder in node.folders:
            submenu = menu.addMenu(folder.label.replace("&", "&&"))
            submenu.setToolTipsVisible(True)
            if folder.path:
                submenu.setToolTip(folder.path)
                submenu.setStatusTip(folder.path)
            self._populate_folder_menu(submenu, folder)
        for bookmark in node.bookmarks:
            action = menu.addAction(bookmark.label.replace("&", "&&"))
            action.setToolTip(display_path_text(bookmark.path))
            action.setStatusTip(display_path_text(bookmark.path))
            action.triggered.connect(self._open_bookmark_callback(bookmark))

    def _prompt_folder_destination(
        self,
        *,
        title: str,
        initial_folder: str,
    ) -> str | None:
        options = [self.ROOT_FOLDER_LABEL, *self.folder_paths, self.CREATE_FOLDER_LABEL]
        initial_choice = self.ROOT_FOLDER_LABEL
        normalized_initial = normalize_bookmark_folder_path(initial_folder)
        if normalized_initial and normalized_initial in options:
            initial_choice = normalized_initial
        initial_index = options.index(initial_choice)
        selected_raw, accepted = QInputDialog.getItem(
            self.window,
            title,
            "Bookmark folder:",
            options,
            initial_index,
            False,
        )
        if not accepted:
            return None
        selected = str(selected_raw).strip()
        if selected == self.ROOT_FOLDER_LABEL:
            return ""
        if selected == self.CREATE_FOLDER_LABEL:
            folder_path, folder_accepted = QInputDialog.getText(
                self.window,
                title,
                "New folder path:",
            )
            if not folder_accepted:
                return None
            normalized = normalize_bookmark_folder_path(folder_path)
            if not normalized:
                return None
            return normalized
        return normalize_bookmark_folder_path(selected)

    def _open_bookmark_in_active_tab(self, path: Path) -> None:
        panel = self.window.panels_coordinator.active_panel()
        if panel is None:
            return
        current_tab = panel.current_tab()
        if current_tab is None:
            return
        current_tab.navigation.set_path(path)
        current_tab.view.setFocus()

    def _open_bookmark_in_new_tab(self, path: Path) -> None:
        panel = self.window.panels_coordinator.active_panel()
        if panel is None:
            return
        tab = panel.add_tab(path)
        tab.view.setFocus()

    def _open_bookmark_in_new_window(self, path: Path) -> None:
        new_window = self.window.controller.new_window(
            from_window=self.window,
            show=False,
        )
        panel = new_window.panels_coordinator.active_panel()
        if panel is not None:
            current_tab = panel.current_tab()
            if current_tab is not None:
                current_tab.navigation.set_path(path)
                current_tab.view.setFocus()
        new_window.show()

    def _reload_bookmarks(self, *, report_errors: bool) -> None:
        """Reload bookmarks from disk and refresh file watching."""

        try:
            self._collection = self._store.load()
        except RuntimeError as exc:
            if report_errors:
                self._show_status_message(str(exc), 3200)
            self._refresh_watch_paths()
            return
        self._tree = build_bookmark_tree(self._collection)
        self._refresh_watch_paths()

    def _refresh_watch_paths(self) -> None:
        """Align file-system watches with the current bookmarks file state."""

        parent_dir = self._store.bookmarks_file.parent
        watched_paths = self._watcher.files() + self._watcher.directories()
        current_paths = {str(path) for path in watched_paths}
        desired_paths = {str(parent_dir)}
        if self._store.bookmarks_file.exists():
            desired_paths.add(str(self._store.bookmarks_file))

        remove_paths = sorted(current_paths - desired_paths)
        if remove_paths:
            self._watcher.removePaths(remove_paths)
        add_paths = sorted(desired_paths - current_paths)
        if add_paths:
            self._watcher.addPaths(add_paths)

    def _current_bookmark(self) -> Bookmark | None:
        current_path = self._current_bookmark_path()
        if current_path is None:
            return None
        return self._bookmark_for_path(current_path)

    def _current_bookmark_path(self) -> Path | None:
        active_panel = self.window.panels_coordinator.active_panel()
        if active_panel is None:
            return None
        return active_panel.current_path()

    def _bookmark_for_path(self, path: Path) -> Bookmark | None:
        target_key = path_key(Path(path))
        for bookmark in self._collection.bookmarks:
            if path_key(bookmark.path) == target_key:
                return bookmark
        return None

    def _open_bookmark_callback(self, bookmark: Bookmark) -> Callable[[bool], None]:
        """Build a stable callback for one bookmark action."""

        def _handle_triggered(_checked: bool = False) -> None:
            self.open_bookmark(bookmark)

        return _handle_triggered

    def _on_bookmarks_fs_changed(self, _path: str) -> None:
        """Reload bookmarks after an external edit or file-creation change."""

        self._reload_bookmarks(report_errors=True)

    def _show_status_message(self, message: str, timeout_ms: int) -> None:
        """Show one transient status-bar message."""

        self.window.statusBar().showMessage(message, timeout_ms)
