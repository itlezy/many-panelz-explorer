"""Saved-view coordination for explorer windows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QInputDialog, QMenu, QMessageBox

if TYPE_CHECKING:
    from collections.abc import Callable

    from ...window import ExplorerWindow


class WindowViewsCoordinator:
    """Manage saved view creation, replacement, and restoration."""

    def __init__(self, window: ExplorerWindow) -> None:
        """Store the owning window reference."""
        self.window = window

    def save_view(self) -> None:
        """Persist the current window state as a named saved view."""
        name, ok = QInputDialog.getText(self.window, "Save View", "View name:")
        if not ok:
            return
        view_name = name.strip()
        if not view_name:
            return

        existing_view = self.window.persistence_coordinator.saved_view_snapshot(
            view_name
        )
        if existing_view is not None:
            overwrite = QMessageBox.question(
                self.window,
                "Save View",
                f'View "{view_name}" already exists. Overwrite?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if overwrite != QMessageBox.StandardButton.Yes:
                return

        self.window.persistence_coordinator.save_named_view(view_name)

    def restore_view(self) -> None:
        """Open a saved view in a newly created window."""
        view_name = self._prompt_saved_view_name("Restore View")
        if view_name is None:
            return
        self.restore_view_named(view_name)

    def restore_view_named(self, view_name: str) -> None:
        """Open the given saved view name in a newly created window."""
        restored_window = (
            self.window.persistence_coordinator.open_saved_view_in_new_window(view_name)
        )
        if restored_window is None:
            QMessageBox.warning(
                self.window,
                "Restore View",
                f'View "{view_name}" was not found.',
            )
        return

    def replace_view(self) -> None:
        """Replace the current window state with a saved view."""
        view_name = self._prompt_saved_view_name("Replace View")
        if view_name is None:
            return
        if self.window.persistence_coordinator.replace_from_saved_view(view_name):
            return
        QMessageBox.warning(
            self.window,
            "Replace View",
            f'View "{view_name}" was not found.',
        )

    def populate_restore_view_menu(self, menu: QMenu) -> None:
        """Populate the restore-view submenu with saved views."""
        menu.clear()
        names = self.window.persistence_coordinator.saved_view_names()
        if not names:
            empty_action = menu.addAction("(N&o saved views)")
            empty_action.setEnabled(False)
            return

        for view_name in names:
            action = menu.addAction(view_name.replace("&", "&&"))
            action.triggered.connect(self._restore_view_named_callback(view_name))

    def _prompt_saved_view_name(self, title: str) -> str | None:
        """Prompt the user to choose one saved view name."""

        names = self.window.persistence_coordinator.saved_view_names()
        if not names:
            QMessageBox.information(self.window, title, "No saved views.")
            return None

        selected_raw, ok = QInputDialog.getItem(
            self.window,
            title,
            "Select a saved view:",
            names,
            0,
            False,
        )
        selected = str(selected_raw).strip()
        if not ok or not selected:
            return None
        return selected

    def _restore_view_named_callback(self, view_name: str) -> Callable[[bool], None]:
        """Build a callback that restores a fixed saved view name."""

        def _handle_triggered(_checked: bool = False) -> None:
            self.restore_view_named(view_name)

        return _handle_triggered
