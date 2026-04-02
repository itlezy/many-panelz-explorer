"""Dedicated file-list view with split cursor and mark interaction modes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast, override

from PySide6.QtCore import (
    QEvent,
    QItemSelectionModel,
    QModelIndex,
    QPersistentModelIndex,
    QPoint,
    QRect,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor, QContextMenuEvent, QPainter, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTreeView,
    QWidget,
)

from .color_schemes import ResolvedColorScheme, default_color_scheme

if TYPE_CHECKING:
    from PySide6.QtGui import QFocusEvent, QMouseEvent


RIGHT_CLICK_CONTEXT_MENU_DELAY_MS = 1000
type MouseSelectionMode = Literal["right_button", "left_button"]
type HitRegion = Literal["icon", "row", "background"]
type RightDragAction = Literal["mark", "unmark"]


@dataclass(slots=True, frozen=True)
class _RowHit:
    """Describe one pointer hit test against the file list."""

    index: QModelIndex
    region: HitRegion


@dataclass(slots=True, frozen=True)
class FileListColorTokens:
    """Store reusable file-list colors for cursor and mark rendering."""

    background: QColor
    marked_background: QColor
    marked_text: QColor
    focused_current_row_background: QColor
    inactive_current_row_background: QColor
    focused_current_marked_background: QColor
    inactive_current_marked_background: QColor
    current_marked_text: QColor
    hidden_text: QColor


class _ExplorerFileListItemDelegate(QStyledItemDelegate):
    """Paint file-list rows without the default dotted focus rectangle."""

    def __init__(self, owner: ExplorerFileListView) -> None:
        """Initialize the delegate for one explorer file list."""

        super().__init__(owner)
        self._owner = owner

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        """Paint one row with explicit current-row styling."""

        styled_option = self._owner.styled_option_for_index(option, index)
        super().paint(painter, styled_option, index)


class ExplorerFileListView(QTreeView):
    """Render the file list with commander-style mark gestures."""

    delayed_context_menu_requested = Signal(QPoint)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the file-list view and delayed context-menu timer."""

        super().__init__(parent)
        self._enable_right_click_row_selection = True
        self._mouse_selection_mode: MouseSelectionMode = "right_button"
        self._color_tokens = self._build_color_tokens()
        self._pending_right_click_pos = QPoint()
        self._pending_right_click_index = QModelIndex()
        self._pending_right_click_rect = QRect()
        self._right_button_pressed = False
        self._consume_right_button_release = False
        self._right_drag_marked_rows: set[int] = set()
        self._right_drag_action: RightDragAction | None = None
        self._pending_left_mode_context_pos = QPoint()
        self._pending_left_mode_context = False
        self._delayed_context_menu_timer = QTimer(self)
        self._delayed_context_menu_timer.setSingleShot(True)
        self._delayed_context_menu_timer.setInterval(RIGHT_CLICK_CONTEXT_MENU_DELAY_MS)
        self._delayed_context_menu_timer.timeout.connect(
            self._emit_delayed_context_menu_request
        )
        self.setItemDelegate(_ExplorerFileListItemDelegate(self))

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
        self._consume_right_button_release = False

    def file_list_color_tokens(self) -> FileListColorTokens:
        """Return the current file-list state colors."""

        return self._color_tokens

    def apply_color_scheme(self, scheme: ResolvedColorScheme) -> None:
        """Apply one resolved color scheme to the file-list renderer."""

        self._color_tokens = self._build_color_tokens(scheme)
        self.viewport().update()

    def styled_option_for_index(
        self,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QStyleOptionViewItem:
        """Return the delegate style option for one index."""

        styled_option = QStyleOptionViewItem(option)
        model_index = cast("QModelIndex", index)
        delegate = self.itemDelegate()
        if isinstance(delegate, QStyledItemDelegate):
            delegate.initStyleOption(styled_option, model_index)
        row_index = model_index.siblingAtColumn(0)
        current_row_index = self.currentIndex().siblingAtColumn(0)
        styled_option.state &= ~QStyle.StateFlag.State_HasFocus
        marked = self.is_row_marked(row_index)
        current = row_index.isValid() and row_index == current_row_index
        if not current and not marked:
            return styled_option
        background_color, text_color = self._row_state_colors(
            marked=marked,
            current=current,
        )
        styled_option.state |= QStyle.StateFlag.State_Selected
        for group in (
            QPalette.ColorGroup.Active,
            QPalette.ColorGroup.Inactive,
            QPalette.ColorGroup.Normal,
        ):
            styled_option.palette.setColor(
                group,
                QPalette.ColorRole.Highlight,
                background_color,
            )
            styled_option.palette.setColor(
                group,
                QPalette.ColorRole.HighlightedText,
                text_color,
            )
        return styled_option

    def is_row_marked(self, index: QModelIndex) -> bool:
        """Return whether the given row is marked."""

        row_index = index.siblingAtColumn(0)
        if not row_index.isValid():
            return False
        selection_model = self.selectionModel()
        return bool(selection_model.isSelected(row_index))

    def has_active_file_list_focus(self) -> bool:
        """Return whether this file list currently owns focus."""

        return bool(self.hasFocus() or self.viewport().hasFocus())

    @override
    def changeEvent(self, event: QEvent) -> None:
        """Refresh cached colors when the palette or style changes."""

        if event.type() in {
            QEvent.Type.PaletteChange,
            QEvent.Type.ApplicationPaletteChange,
            QEvent.Type.StyleChange,
        }:
            self._color_tokens = self._build_color_tokens()
            self.viewport().update()
        super().changeEvent(event)

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
        """Handle drag marking and delayed-menu cancellation."""

        pos = event.position().toPoint()
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
    def focusInEvent(self, event: QFocusEvent) -> None:
        """Refresh current-row styling when the file list gains focus."""

        super().focusInEvent(event)
        self.viewport().update()

    @override
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Activate the clicked item explicitly when the user double clicks."""

        if event.button() != Qt.MouseButton.LeftButton:
            super().mouseDoubleClickEvent(event)
            return
        index = self.indexAt(event.position().toPoint()).siblingAtColumn(0)
        if not index.isValid():
            event.accept()
            return
        self._set_current_row(index)
        self.scrollTo(index)
        self.activated.emit(index)
        event.accept()

    @override
    def viewportEvent(self, event: QEvent) -> bool:
        """Suppress mouse-originated context menus in commander mode."""

        if (
            self._mouse_selection_mode == "right_button"
            and event.type() == QEvent.Type.ContextMenu
            and isinstance(event, QContextMenuEvent)
            and event.reason() == QContextMenuEvent.Reason.Mouse
        ):
            event.accept()
            return True
        return super().viewportEvent(event)

    @override
    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """Suppress only mouse-originated Qt context menus in commander mode."""

        if (
            self._mouse_selection_mode == "right_button"
            and event.reason() == event.Reason.Mouse
        ):
            event.accept()
            return
        super().contextMenuEvent(event)

    @override
    def focusOutEvent(self, event: QFocusEvent) -> None:
        """Clear pending right-click state on focus loss."""

        self._cancel_pending_right_click()
        self._consume_right_button_release = False
        self._pending_left_mode_context = False
        self._pending_left_mode_context_pos = QPoint()
        super().focusOutEvent(event)
        self.viewport().update()

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
        """Handle icon toggle for left-button mode."""

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
        return False

    def _handle_right_button_mode_right_press(
        self,
        pos: QPoint,
        event: QMouseEvent,
    ) -> bool:
        """Handle mark toggle, drag marking, and hold-to-menu in right mode."""

        hit = self._hit_test(pos)
        if not hit.index.isValid():
            self._cancel_pending_right_click()
            self._consume_right_button_release = True
            event.accept()
            return True
        was_marked = self._is_marked(hit.index)
        self._right_drag_action = "unmark" if was_marked else "mark"
        self._set_current_row(hit.index)
        self._set_mark(hit.index, marked=not was_marked)
        self.scrollTo(hit.index)
        self._pending_right_click_pos = QPoint(pos)
        self._pending_right_click_index = QModelIndex(hit.index)
        self._pending_right_click_rect = QRect(self.visualRect(hit.index))
        self._right_button_pressed = True
        self._consume_right_button_release = True
        self._right_drag_marked_rows = {hit.index.row()}
        self._delayed_context_menu_timer.start()
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
            return _RowHit(row_index, "row")
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

    def _handle_right_button_drag(self, pos: QPoint) -> None:
        """Propagate the starting mark action across rows crossed by the drag."""

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
        if (
            hit.index.row() not in self._right_drag_marked_rows
            and self._right_drag_action is not None
        ):
            self._set_mark(hit.index, marked=self._right_drag_action == "mark")
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

    def _set_mark(self, index: QModelIndex, *, marked: bool) -> bool:
        """Set one row mark explicitly and return whether it is marked afterwards."""

        row_index = index.siblingAtColumn(0)
        if not row_index.isValid():
            return False
        selection_flag = (
            QItemSelectionModel.SelectionFlag.Select
            if marked
            else QItemSelectionModel.SelectionFlag.Deselect
        )
        self.selectionModel().select(
            row_index,
            selection_flag | QItemSelectionModel.SelectionFlag.Rows,
        )
        return self.selectionModel().isSelected(row_index)

    def _is_marked(self, index: QModelIndex) -> bool:
        """Return whether one row is currently marked."""

        row_index = index.siblingAtColumn(0)
        if not row_index.isValid():
            return False
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
        self._right_drag_action = None

    def _build_color_tokens(
        self,
        scheme: ResolvedColorScheme | None = None,
    ) -> FileListColorTokens:
        """Build file-list colors from the current palette."""

        resolved = scheme or default_color_scheme()
        return FileListColorTokens(
            background=QColor(resolved.file_list_background_hex),
            marked_background=QColor(resolved.file_list_marked_background_hex),
            marked_text=QColor(resolved.file_list_marked_text_hex),
            focused_current_row_background=QColor(
                resolved.file_list_current_focused_background_hex
            ),
            inactive_current_row_background=QColor(
                resolved.file_list_current_inactive_background_hex
            ),
            focused_current_marked_background=QColor(
                resolved.file_list_current_marked_focused_background_hex
            ),
            inactive_current_marked_background=QColor(
                resolved.file_list_current_marked_inactive_background_hex
            ),
            current_marked_text=QColor(resolved.file_list_current_marked_text_hex),
            hidden_text=QColor(resolved.file_list_hidden_text_hex),
        )

    def _row_state_colors(
        self,
        *,
        marked: bool,
        current: bool,
    ) -> tuple[QColor, QColor]:
        """Return background and text colors for one row state."""

        tokens = self._color_tokens
        palette = self.palette()
        default_text = palette.color(QPalette.ColorRole.Text)
        if marked and current:
            return (
                (
                    tokens.focused_current_marked_background
                    if self.has_active_file_list_focus()
                    else tokens.inactive_current_marked_background
                ),
                tokens.current_marked_text,
            )
        if marked:
            return (tokens.marked_background, tokens.marked_text)
        return (
            (
                tokens.focused_current_row_background
                if self.has_active_file_list_focus()
                else tokens.inactive_current_row_background
            ),
            default_text,
        )
