"""Dedicated file-list view with commander-style mouse selection helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtCore import QItemSelectionModel, QModelIndex, QPoint, Qt, QTimer, Signal
from PySide6.QtWidgets import QTreeView, QWidget

if TYPE_CHECKING:
    from PySide6.QtGui import QFocusEvent, QMouseEvent


RIGHT_CLICK_CONTEXT_MENU_DELAY_MS = 1000


class ExplorerFileListView(QTreeView):
    """Render the file list with custom left-click and optional right-click logic."""

    delayed_context_menu_requested = Signal(QPoint)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the file-list view and delayed context-menu timer."""

        super().__init__(parent)
        self._enable_right_click_row_selection = True
        self._pending_right_click_pos = QPoint()
        self._pending_right_click_index = QModelIndex()
        self._right_button_pressed = False
        self._consume_right_button_release = False
        self._delayed_context_menu_timer = QTimer(self)
        self._delayed_context_menu_timer.setSingleShot(True)
        self._delayed_context_menu_timer.setInterval(RIGHT_CLICK_CONTEXT_MENU_DELAY_MS)
        self._delayed_context_menu_timer.timeout.connect(
            self._emit_delayed_context_menu_request
        )

    @property
    def enable_right_click_row_selection(self) -> bool:
        """Return whether right-click row selection is currently enabled."""

        return bool(self._enable_right_click_row_selection)

    def set_enable_right_click_row_selection(self, enabled: bool) -> None:
        """Enable or disable delayed right-click row selection behavior."""

        self._enable_right_click_row_selection = bool(enabled)
        if not self._enable_right_click_row_selection:
            self._cancel_pending_right_click()
            self._consume_right_button_release = False

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Apply commander-style mouse behavior before falling back to Qt defaults."""

        if event.button() == Qt.MouseButton.LeftButton:
            if self._apply_left_click_selection(event.position().toPoint(), event):
                return
            super().mousePressEvent(event)
            return
        if event.button() == Qt.MouseButton.RightButton:
            if self._enable_right_click_row_selection and (
                self._apply_right_click_selection(event.position().toPoint(), event)
            ):
                return
            super().mousePressEvent(event)
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Cancel a pending delayed context menu when the pointer leaves the row."""

        if (
            self._right_button_pressed
            and self._delayed_context_menu_timer.isActive()
            and self._pending_right_click_index.isValid()
        ):
            index = self.indexAt(event.position().toPoint())
            row_index = index.siblingAtColumn(0) if index.isValid() else QModelIndex()
            if row_index != self._pending_right_click_index:
                self._cancel_pending_right_click()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Cancel a delayed context-menu request when the right button is released."""

        if event.button() == Qt.MouseButton.RightButton and self._right_button_pressed:
            self._cancel_pending_right_click()
            self._consume_right_button_release = False
            event.accept()
            return
        if (
            event.button() == Qt.MouseButton.RightButton
            and self._consume_right_button_release
        ):
            self._consume_right_button_release = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    @override
    def focusOutEvent(self, event: QFocusEvent) -> None:
        """Clear pending right-click menu state when the view loses focus."""

        self._cancel_pending_right_click()
        self._consume_right_button_release = False
        super().focusOutEvent(event)

    def _apply_left_click_selection(self, pos: QPoint, event: QMouseEvent) -> bool:
        """Apply commander-style left-click selection for one file-list row."""

        row_index = self._real_row_index_at(pos)
        if not row_index.isValid():
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
        selection_model.setCurrentIndex(
            row_index,
            QItemSelectionModel.SelectionFlag.ClearAndSelect
            | QItemSelectionModel.SelectionFlag.Rows,
        )
        event.accept()
        return True

    def _apply_right_click_selection(self, pos: QPoint, event: QMouseEvent) -> bool:
        """Apply delayed right-click selection and menu behavior for one row."""

        row_index = self._real_row_index_at(pos)
        if not row_index.isValid():
            return False
        selection_model = self.selectionModel()
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
        self._pending_right_click_pos = QPoint(pos)
        self._pending_right_click_index = QModelIndex(row_index)
        self._right_button_pressed = True
        self._consume_right_button_release = True
        self._delayed_context_menu_timer.start()
        event.accept()
        return True

    def _real_row_index_at(self, pos: QPoint) -> QModelIndex:
        """Return the row index for one real file-list item at the viewport position."""

        model = self.model()
        index = self.indexAt(pos)
        if not index.isValid():
            return QModelIndex()
        row_index = index.siblingAtColumn(0)
        if not row_index.isValid():
            return QModelIndex()
        is_parent_index = getattr(model, "is_parent_index", None)
        if callable(is_parent_index) and bool(is_parent_index(row_index)):
            return QModelIndex()
        return row_index

    def _emit_delayed_context_menu_request(self) -> None:
        """Emit the delayed context-menu request when the press-and-hold completes."""

        if (
            not self._right_button_pressed
            or not self._pending_right_click_index.isValid()
        ):
            return
        current_index = self.currentIndex().siblingAtColumn(0)
        if current_index != self._pending_right_click_index:
            self._cancel_pending_right_click()
            return
        pos = QPoint(self._pending_right_click_pos)
        self._cancel_pending_right_click()
        self.delayed_context_menu_requested.emit(pos)

    def _cancel_pending_right_click(self) -> None:
        """Reset any pending delayed context-menu request state."""

        self._delayed_context_menu_timer.stop()
        self._pending_right_click_pos = QPoint()
        self._pending_right_click_index = QModelIndex()
        self._right_button_pressed = False
