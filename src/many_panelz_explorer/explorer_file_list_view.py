"""Dedicated file-list view with split cursor and mark interaction modes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, override

from PySide6.QtCore import (
    QItemSelectionModel,
    QModelIndex,
    QPoint,
    QRect,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtWidgets import QApplication, QRubberBand, QTreeView, QWidget

if TYPE_CHECKING:
    from PySide6.QtGui import QContextMenuEvent, QFocusEvent, QMouseEvent


RIGHT_CLICK_CONTEXT_MENU_DELAY_MS = 1000
type MouseSelectionMode = Literal["right_button", "left_button"]
type HitRegion = Literal["icon", "row", "behind_name", "background"]


@dataclass(slots=True, frozen=True)
class _RowHit:
    """Describe one pointer hit test against the file list."""

    index: QModelIndex
    region: HitRegion


class ExplorerFileListView(QTreeView):
    """Render the file list with commander-style mark gestures."""

    delayed_context_menu_requested = Signal(QPoint)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the file-list view and delayed context-menu timer."""

        super().__init__(parent)
        self._enable_right_click_row_selection = True
        self._mouse_selection_mode: MouseSelectionMode = "right_button"
        self._pending_right_click_pos = QPoint()
        self._pending_right_click_index = QModelIndex()
        self._pending_right_click_rect = QRect()
        self._right_button_pressed = False
        self._consume_right_button_release = False
        self._right_drag_marked_rows: set[int] = set()
        self._pending_left_mode_context_pos = QPoint()
        self._pending_left_mode_context = False
        self._pending_band_origin: QPoint | None = None
        self._pending_band_button = Qt.MouseButton.NoButton
        self._pending_band_additive = False
        self._rubber_band_anchor_index = QModelIndex()
        self._rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self.viewport())
        self._rubber_band.hide()
        self._rubber_band_active = False
        self._rubber_band_button = Qt.MouseButton.NoButton
        self._rubber_band_additive = False
        self._delayed_context_menu_timer = QTimer(self)
        self._delayed_context_menu_timer.setSingleShot(True)
        self._delayed_context_menu_timer.setInterval(RIGHT_CLICK_CONTEXT_MENU_DELAY_MS)
        self._delayed_context_menu_timer.timeout.connect(
            self._emit_delayed_context_menu_request
        )

    @property
    def enable_right_click_row_selection(self) -> bool:
        """Return whether right-button marking mode is currently enabled."""

        return bool(self._enable_right_click_row_selection)

    @property
    def mouse_selection_mode(self) -> MouseSelectionMode:
        """Return the active file-list mouse selection mode."""

        return self._mouse_selection_mode

    def set_enable_right_click_row_selection(self, enabled: bool) -> None:
        """Apply the legacy boolean as the active mouse selection mode."""

        self._enable_right_click_row_selection = bool(enabled)
        self.set_mouse_selection_mode(
            "right_button" if self._enable_right_click_row_selection else "left_button"
        )

    def set_mouse_selection_mode(self, mode: str) -> None:
        """Set the explicit mouse selection mode for the file list."""

        normalized_mode = (
            "right_button"
            if str(mode).strip().lower() == "right_button"
            else "left_button"
        )
        self._mouse_selection_mode = normalized_mode
        self._enable_right_click_row_selection = normalized_mode == "right_button"
        self._cancel_pending_right_click()
        self._cancel_rubber_band()
        self._consume_right_button_release = False

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Interpret file-list press gestures before falling back to Qt defaults."""

        pos = event.position().toPoint()
        if event.button() == Qt.MouseButton.LeftButton:
            if self._mouse_selection_mode == "right_button":
                if self._handle_right_button_mode_left_press(pos, event):
                    return
            elif self._handle_left_button_mode_left_press(pos, event):
                return
            super().mousePressEvent(event)
            return
        if event.button() == Qt.MouseButton.RightButton:
            if self._mouse_selection_mode == "right_button":
                if self._handle_right_button_mode_right_press(pos, event):
                    return
            elif self._handle_left_button_mode_right_press(pos, event):
                return
            super().mousePressEvent(event)
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle drag marking, rubberbanding, and delayed-menu cancellation."""

        pos = event.position().toPoint()
        if self._maybe_start_pending_rubber_band(pos, event):
            event.accept()
            return
        if self._rubber_band_active:
            self._update_rubber_band(pos)
            event.accept()
            return
        if (
            self._mouse_selection_mode == "right_button"
            and bool(event.buttons() & Qt.MouseButton.RightButton)
            and self._right_button_pressed
        ):
            self._handle_right_button_drag(pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Finalize custom mark gestures and suppress unwanted default menus."""

        button = event.button()
        if self._rubber_band_active and button == self._rubber_band_button:
            self._cancel_rubber_band()
            event.accept()
            return
        if self._pending_band_button == button:
            self._clear_pending_band()
            event.accept()
            return
        if (
            self._mouse_selection_mode == "right_button"
            and button == Qt.MouseButton.RightButton
            and self._right_button_pressed
        ):
            self._cancel_pending_right_click()
            self._consume_right_button_release = False
            event.accept()
            return
        if button == Qt.MouseButton.RightButton and self._consume_right_button_release:
            self._consume_right_button_release = False
            event.accept()
            return
        if (
            self._mouse_selection_mode == "left_button"
            and button == Qt.MouseButton.RightButton
            and self._pending_left_mode_context
        ):
            pos = QPoint(self._pending_left_mode_context_pos)
            self._pending_left_mode_context = False
            self._pending_left_mode_context_pos = QPoint()
            self.customContextMenuRequested.emit(pos)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    @override
    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """Suppress Qt's immediate right-click menu in commander mouse mode."""

        if self._mouse_selection_mode == "right_button":
            event.accept()
            return
        super().contextMenuEvent(event)

    @override
    def focusOutEvent(self, event: QFocusEvent) -> None:
        """Clear pending right-click and rubberband state on focus loss."""

        self._cancel_pending_right_click()
        self._cancel_rubber_band()
        self._consume_right_button_release = False
        self._pending_left_mode_context = False
        self._pending_left_mode_context_pos = QPoint()
        super().focusOutEvent(event)

    def _handle_right_button_mode_left_press(
        self,
        pos: QPoint,
        event: QMouseEvent,
    ) -> bool:
        """Handle cursor-only and mark gestures for right-button mode."""

        hit = self._hit_test(pos)
        if hit.region == "background":
            event.accept()
            return True
        if hit.region == "icon":
            self._set_current_row(hit.index)
            self._toggle_mark(hit.index)
            event.accept()
            return True
        if not hit.index.isValid():
            event.accept()
            return True
        modifiers = event.modifiers()
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            self._mark_range_from_current(hit.index)
            self._set_current_row(hit.index)
            self.scrollTo(hit.index)
            event.accept()
            return True
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            self._set_current_row(hit.index)
            self._toggle_mark(hit.index)
            self.scrollTo(hit.index)
            event.accept()
            return True
        self._set_current_row(hit.index)
        self.scrollTo(hit.index)
        event.accept()
        return True

    def _handle_left_button_mode_left_press(
        self,
        pos: QPoint,
        event: QMouseEvent,
    ) -> bool:
        """Handle icon toggle and rubberband start for left-button mode."""

        hit = self._hit_test(pos)
        if hit.region == "background":
            event.accept()
            return True
        if hit.region == "icon" and hit.index.isValid():
            self._set_current_row(hit.index)
            self._toggle_mark(hit.index)
            self.scrollTo(hit.index)
            event.accept()
            return True
        if hit.region == "behind_name" and hit.index.isValid():
            self._set_current_row(hit.index)
            self._prepare_pending_band(
                origin=pos,
                button=Qt.MouseButton.LeftButton,
                anchor_index=hit.index,
                additive=False,
            )
            event.accept()
            return True
        return False

    def _handle_right_button_mode_right_press(
        self,
        pos: QPoint,
        event: QMouseEvent,
    ) -> bool:
        """Handle mark toggle, drag marking, and hold-to-menu in right mode."""

        hit = self._hit_test(pos)
        if not hit.index.isValid():
            return False
        self._set_current_row(hit.index)
        self._toggle_mark(hit.index)
        self.scrollTo(hit.index)
        self._pending_right_click_pos = QPoint(pos)
        self._pending_right_click_index = QModelIndex(hit.index)
        self._pending_right_click_rect = QRect(self.visualRect(hit.index))
        self._right_button_pressed = True
        self._consume_right_button_release = True
        self._right_drag_marked_rows = {hit.index.row()}
        self._delayed_context_menu_timer.start()
        if hit.region == "behind_name":
            self._prepare_pending_band(
                origin=pos,
                button=Qt.MouseButton.RightButton,
                anchor_index=hit.index,
                additive=True,
            )
        event.accept()
        return True

    def _handle_left_button_mode_right_press(
        self,
        pos: QPoint,
        event: QMouseEvent,
    ) -> bool:
        """Open the normal context menu without changing marked rows."""

        hit = self._hit_test(pos)
        if hit.index.isValid():
            self._set_current_row(hit.index)
            self.scrollTo(hit.index)
        self._pending_left_mode_context_pos = QPoint(pos)
        self._pending_left_mode_context = True
        event.accept()
        return True

    def _hit_test(self, pos: QPoint) -> _RowHit:
        """Return the hit region for one viewport position."""

        row_index = self._real_row_index_at(pos)
        if not row_index.isValid():
            return _RowHit(QModelIndex(), "background")
        cell_rect = self.visualRect(row_index)
        icon_width = max(12, int(self.iconSize().width()))
        icon_rect = QRect(
            cell_rect.left(),
            cell_rect.top(),
            icon_width + 8,
            cell_rect.height(),
        )
        if icon_rect.contains(pos):
            return _RowHit(row_index, "icon")
        display_value = row_index.data(int(Qt.ItemDataRole.DisplayRole))
        display_text = str(display_value or "")
        text_start = icon_rect.right() + 4
        text_width = self.fontMetrics().horizontalAdvance(display_text)
        text_end = min(cell_rect.right(), text_start + text_width)
        if pos.x() > text_end:
            return _RowHit(row_index, "behind_name")
        return _RowHit(row_index, "row")

    def _real_row_index_at(self, pos: QPoint) -> QModelIndex:
        """Return the row index for one real file-list item at the given position."""

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

    def _prepare_pending_band(
        self,
        *,
        origin: QPoint,
        button: Qt.MouseButton,
        anchor_index: QModelIndex,
        additive: bool,
    ) -> None:
        """Store a possible rubberband start until drag threshold is reached."""

        self._pending_band_origin = QPoint(origin)
        self._pending_band_button = button
        self._pending_band_additive = bool(additive)
        self._rubber_band_anchor_index = QModelIndex(anchor_index)

    def _maybe_start_pending_rubber_band(
        self,
        pos: QPoint,
        event: QMouseEvent,
    ) -> bool:
        """Start the pending rubberband once the drag threshold is exceeded."""

        origin = self._pending_band_origin
        if origin is None:
            return False
        if not bool(event.buttons() & self._pending_band_button):
            self._clear_pending_band()
            return False
        if (pos - origin).manhattanLength() < QApplication.startDragDistance():
            return False
        self._cancel_pending_right_click()
        self._rubber_band_active = True
        self._rubber_band_button = self._pending_band_button
        self._rubber_band_additive = self._pending_band_additive
        rubber_rect = QRect(origin, pos).normalized()
        self._rubber_band.setGeometry(rubber_rect)
        self._rubber_band.show()
        self._update_rubber_band(pos)
        self._clear_pending_band()
        return True

    def _update_rubber_band(self, pos: QPoint) -> None:
        """Refresh rubberband geometry and mark rows intersecting it."""

        origin = self._rubber_band.geometry().topLeft()
        rubber_rect = QRect(origin, pos).normalized()
        self._rubber_band.setGeometry(rubber_rect)
        intersected = self._intersected_real_rows(rubber_rect)
        selection_model = self.selectionModel()
        if not self._rubber_band_additive:
            selection_model.clearSelection()
        for row_index in intersected:
            selection_model.select(
                row_index,
                QItemSelectionModel.SelectionFlag.Select
                | QItemSelectionModel.SelectionFlag.Rows,
            )
        if self._rubber_band_anchor_index.isValid():
            self._set_current_row(self._rubber_band_anchor_index)

    def _intersected_real_rows(self, rubber_rect: QRect) -> list[QModelIndex]:
        """Return real row indexes whose visual rects intersect the band."""

        rows: list[QModelIndex] = []
        root_index = self.rootIndex()
        for row in range(self.model().rowCount(root_index)):
            candidate = self.model().index(row, 0, root_index)
            if not candidate.isValid():
                continue
            row_index = candidate.siblingAtColumn(0)
            if not row_index.isValid():
                continue
            if self._is_parent_index(row_index):
                continue
            if self.visualRect(row_index).intersects(rubber_rect):
                rows.append(row_index)
        return rows

    def _handle_right_button_drag(self, pos: QPoint) -> None:
        """Additively mark rows crossed by the right mouse button."""

        if self._delayed_context_menu_timer.isActive() and (
            not self._pending_right_click_rect.contains(pos)
            or (pos - self._pending_right_click_pos).manhattanLength()
            >= QApplication.startDragDistance()
        ):
            self._delayed_context_menu_timer.stop()
        hit = self._hit_test(pos)
        if not hit.index.isValid():
            return
        self._set_current_row(hit.index)
        if hit.index.row() not in self._right_drag_marked_rows:
            self.selectionModel().select(
                hit.index,
                QItemSelectionModel.SelectionFlag.Select
                | QItemSelectionModel.SelectionFlag.Rows,
            )
            self._right_drag_marked_rows.add(hit.index.row())
        self.scrollTo(hit.index)

    def _set_current_row(self, index: QModelIndex) -> None:
        """Move the cursor to one row without changing existing marks."""

        row_index = index.siblingAtColumn(0)
        if not row_index.isValid():
            return
        self.selectionModel().setCurrentIndex(
            row_index,
            QItemSelectionModel.SelectionFlag.Current,
        )

    def _toggle_mark(self, index: QModelIndex) -> bool:
        """Toggle one row mark and return whether it is marked afterwards."""

        row_index = index.siblingAtColumn(0)
        if not row_index.isValid():
            return False
        self.selectionModel().select(
            row_index,
            QItemSelectionModel.SelectionFlag.Toggle
            | QItemSelectionModel.SelectionFlag.Rows,
        )
        return self.selectionModel().isSelected(row_index)

    def _mark_range_from_current(self, end_index: QModelIndex) -> None:
        """Additively mark the range from the current row to the target row."""

        start_index = self.currentIndex().siblingAtColumn(0)
        final_index = end_index.siblingAtColumn(0)
        if not start_index.isValid() or self._is_parent_index(start_index):
            self._set_current_row(final_index)
            return
        first_row = min(start_index.row(), final_index.row())
        last_row = max(start_index.row(), final_index.row())
        root_index = self.rootIndex()
        for row in range(first_row, last_row + 1):
            candidate = self.model().index(row, 0, root_index)
            if not candidate.isValid() or self._is_parent_index(candidate):
                continue
            self.selectionModel().select(
                candidate,
                QItemSelectionModel.SelectionFlag.Select
                | QItemSelectionModel.SelectionFlag.Rows,
            )

    def _is_parent_index(self, index: QModelIndex) -> bool:
        """Return whether the given index represents the synthetic parent row."""

        is_parent_index = getattr(self.model(), "is_parent_index", None)
        return bool(callable(is_parent_index) and is_parent_index(index))

    def _emit_delayed_context_menu_request(self) -> None:
        """Emit the delayed context-menu request when the hold timer completes."""

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
        self._consume_right_button_release = True
        self.delayed_context_menu_requested.emit(pos)

    def _cancel_pending_right_click(self) -> None:
        """Reset any pending delayed context-menu request state."""

        self._delayed_context_menu_timer.stop()
        self._pending_right_click_pos = QPoint()
        self._pending_right_click_index = QModelIndex()
        self._pending_right_click_rect = QRect()
        self._right_button_pressed = False
        self._right_drag_marked_rows = set()

    def _clear_pending_band(self) -> None:
        """Drop a not-yet-started rubberband candidate."""

        self._pending_band_origin = None
        self._pending_band_button = Qt.MouseButton.NoButton
        self._pending_band_additive = False

    def _cancel_rubber_band(self) -> None:
        """Hide and reset the active rubberband selection."""

        self._rubber_band.hide()
        self._rubber_band_active = False
        self._rubber_band_button = Qt.MouseButton.NoButton
        self._rubber_band_additive = False
        self._rubber_band_anchor_index = QModelIndex()
        self._clear_pending_band()
