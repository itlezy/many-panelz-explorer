"""Dedicated file-list view with opt-in Total Commander mouse semantics."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QItemSelectionModel, QPoint, Qt
from PySide6.QtWidgets import QTreeView, QWidget

if TYPE_CHECKING:
    from PySide6.QtGui import QMouseEvent


FILE_LIST_MOUSE_SELECTION_MODE_QT_DEFAULT = "qt_default"
FILE_LIST_MOUSE_SELECTION_MODE_TC_FULL = "tc_full"


class ExplorerFileListView(QTreeView):
    """Render the file list with optional commander-style mouse selection."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the file-list view with default Qt mouse behavior."""

        super().__init__(parent)
        self._mouse_selection_mode = FILE_LIST_MOUSE_SELECTION_MODE_QT_DEFAULT

    @property
    def mouse_selection_mode(self) -> str:
        """Return the configured mouse-selection behavior identifier."""

        return str(self._mouse_selection_mode)

    def set_mouse_selection_mode(self, mode: str) -> None:
        """Apply a supported mouse-selection behavior identifier."""

        normalized = str(mode or "").strip().lower()
        if normalized not in {
            FILE_LIST_MOUSE_SELECTION_MODE_QT_DEFAULT,
            FILE_LIST_MOUSE_SELECTION_MODE_TC_FULL,
        }:
            normalized = FILE_LIST_MOUSE_SELECTION_MODE_QT_DEFAULT
        self._mouse_selection_mode = normalized

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Apply optional commander-style row selection before Qt defaults."""

        if self._mouse_selection_mode != FILE_LIST_MOUSE_SELECTION_MODE_TC_FULL:
            super().mousePressEvent(event)
            return
        if event.button() not in {
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.RightButton,
        }:
            super().mousePressEvent(event)
            return
        if self._apply_tc_mouse_selection(event.position().toPoint(), event):
            return
        super().mousePressEvent(event)

    def _apply_tc_mouse_selection(self, pos: QPoint, event: QMouseEvent) -> bool:
        """Handle one mouse press using TC-style row-selection rules."""

        model = self.model()
        index = self.indexAt(pos)
        if not index.isValid():
            if event.button() == Qt.MouseButton.RightButton:
                event.accept()
                return True
            return False
        row_index = index.siblingAtColumn(0)
        if not row_index.isValid():
            return False
        is_parent_index = getattr(model, "is_parent_index", None)
        if callable(is_parent_index) and bool(is_parent_index(row_index)):
            return False
        selection_model = self.selectionModel()
        modifiers = event.modifiers()
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            selection_model.setCurrentIndex(
                row_index,
                QItemSelectionModel.SelectionFlag.Current,
            )
            return False
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            selection_model.select(
                row_index,
                QItemSelectionModel.SelectionFlag.Toggle
                | QItemSelectionModel.SelectionFlag.Rows,
            )
            selection_model.setCurrentIndex(
                row_index,
                QItemSelectionModel.SelectionFlag.Current,
            )
            event.accept()
            return True
        if event.button() == Qt.MouseButton.RightButton:
            if selection_model.isSelected(row_index):
                selection_model.setCurrentIndex(
                    row_index,
                    QItemSelectionModel.SelectionFlag.Current,
                )
            else:
                selection_model.setCurrentIndex(
                    row_index,
                    QItemSelectionModel.SelectionFlag.ClearAndSelect
                    | QItemSelectionModel.SelectionFlag.Rows,
                )
            event.accept()
            return True
        selection_model.setCurrentIndex(
            row_index,
            QItemSelectionModel.SelectionFlag.ClearAndSelect
            | QItemSelectionModel.SelectionFlag.Rows,
        )
        event.accept()
        return True
