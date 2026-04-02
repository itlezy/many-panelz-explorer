"""Navigation history and current-row restoration for explorer tabs."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QDir, QItemSelectionModel, QObject, QTimer, Signal
from PySide6.QtWidgets import QAbstractItemView, QTreeView, QWidget
from shiboken6 import isValid
from threep_commons.fs_paths import coerce_path, is_drive_root, path_key

if TYPE_CHECKING:
    from ._explorer_tab_columns import ExplorerTabColumns
    from .fast_dir_model import FastDirModel


class ExplorerTabNavigation(QObject):
    """Manage path history, filters, and current-row restore for a tab."""

    changed = Signal()

    _SELECTION_RESTORE_INTERVAL_MS = 25
    _SELECTION_RESTORE_ATTEMPTS = 40

    def __init__(
        self,
        *,
        owner: QWidget,
        model: FastDirModel,
        view: QTreeView,
        columns: ExplorerTabColumns,
        show_hidden: bool,
        show_system_files: bool,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._owner = owner
        self._model = model
        self._view = view
        self._columns = columns
        self._history: list[Path] = []
        self._history_index = -1
        self._show_hidden = bool(show_hidden)
        self._show_system_files = bool(show_system_files)
        self._current_row_memory: dict[str, Path] = {}
        self._selection_restore_token = 0
        self._show_parent_entry = True
        self._show_parent_dir_at_drive_root = True
        self._inline_filter_text = ""
        self._apply_model_filters()

    @property
    def path(self) -> Path:
        if not self._history:
            return Path.home()
        return self._history[self._history_index]

    @property
    def can_go_back(self) -> bool:
        return self._history_index > 0

    @property
    def can_go_forward(self) -> bool:
        return self._history_index >= 0 and self._history_index < len(self._history) - 1

    @property
    def history(self) -> tuple[Path, ...]:
        return tuple(self._history)

    @property
    def history_index(self) -> int:
        return self._history_index

    @property
    def inline_filter_text(self) -> str:
        return self._inline_filter_text

    def set_show_hidden(self, enabled: bool) -> None:
        self._show_hidden = bool(enabled)
        self._apply_model_filters()
        self.refresh()

    def set_show_system_files(self, enabled: bool) -> None:
        """Update system-file visibility and refresh the active path."""

        self._show_system_files = bool(enabled)
        self._apply_model_filters()
        self.refresh()

    def set_show_parent_dir_at_drive_root(self, enabled: bool) -> None:
        """Update whether drive roots expose a synthetic parent row."""

        self._show_parent_dir_at_drive_root = bool(enabled)
        self._show_parent_entry = self._should_show_parent_entry(self.path)
        self._apply_model_filters()
        if not self._history:
            return
        self.refresh()

    def set_inline_filter(self, text: str) -> None:
        normalized = str(text or "").strip()
        if normalized == self._inline_filter_text:
            return
        self._inline_filter_text = normalized
        self._apply_model_filters()
        self.changed.emit()

    def clear_inline_filter(self) -> None:
        self.set_inline_filter("")

    def set_path(
        self,
        path: Path | str,
        *,
        push_history: bool = True,
        selection_hint: Path | None = None,
    ) -> None:
        target = coerce_path(path)
        if not target.exists() or not target.is_dir():
            target = Path.home()
        previous_path = self.path if self._history else None
        if previous_path is not None:
            self._remember_current_row_for_path(previous_path)
        prepare_for_path_change = getattr(self._owner, "prepare_for_path_change", None)
        if callable(prepare_for_path_change):
            prepare_for_path_change(previous_path, target)

        self._show_parent_entry = self._should_show_parent_entry(target)
        self._apply_model_filters()

        if push_history:
            if not self._history or self._history[self._history_index] != target:
                self._history = self._history[: self._history_index + 1]
                self._history.append(target)
                self._history_index = len(self._history) - 1
        elif not self._history:
            self._history = [target]
            self._history_index = 0

        self._columns.preserve_for_reload()
        index = self._model.setRootPath(str(target))
        self._view.setRootIndex(index)
        self._restore_current_row_for_path(target, preferred=selection_hint)
        self.changed.emit()

    def refresh(self) -> None:
        self.set_path(self.path, push_history=False)

    def go_back(self) -> None:
        if not self.can_go_back:
            return
        self._history_index -= 1
        self.set_path(self._history[self._history_index], push_history=False)

    def go_forward(self) -> None:
        if not self.can_go_forward:
            return
        self._history_index += 1
        self.set_path(self._history[self._history_index], push_history=False)

    def go_up(self) -> None:
        current = self.path
        if self._should_show_drive_root_parent_picker(current):
            show_parent_picker = getattr(
                self._owner,
                "show_drive_root_parent_picker",
                None,
            )
            if callable(show_parent_picker):
                show_parent_picker()
            return
        parent = current.parent
        if parent != current:
            self.set_path(parent, selection_hint=current)

    def go_to_history_index(self, index: int) -> None:
        if index < 0 or index >= len(self._history):
            return
        self._history_index = index
        self.set_path(self._history[self._history_index], push_history=False)

    def _apply_model_filters(self) -> None:
        filters: Any = QDir.Filter.AllEntries | QDir.Filter.AllDirs | QDir.Filter.NoDot
        if not self._show_parent_entry:
            filters |= QDir.Filter.NoDotDot
        if self._show_hidden:
            filters |= QDir.Filter.Hidden
        if self._show_system_files:
            filters |= QDir.Filter.System
        model_any: Any = self._model
        model_any.setFilter(filters)
        if self._inline_filter_text:
            self._model.setNameFilterDisables(False)
            self._model.setNameFilters([f"*{self._inline_filter_text}*"])
            return
        self._model.setNameFilters([])
        self._model.setNameFilterDisables(True)

    def _should_show_parent_entry(self, path: Path) -> bool:
        if self._should_show_drive_root_parent_picker(path):
            return True
        if path.parent == path:
            return False
        return not is_drive_root(path)

    def _should_show_drive_root_parent_picker(self, path: Path) -> bool:
        return self._show_parent_dir_at_drive_root and self._is_windows_drive_root(path)

    def _is_windows_drive_root(self, path: Path) -> bool:
        if os.name != "nt":
            return False
        normalized_path = Path(path)
        anchor = normalized_path.anchor
        return bool(anchor) and normalized_path == Path(anchor)

    def _current_path_or_none(self) -> Path | None:
        index = self._view.currentIndex()
        if not index.isValid() or self._model.is_parent_index(index):
            return None
        return Path(self._model.filePath(index))

    def _remember_current_row_for_path(self, path: Path) -> None:
        current_row_path = self._current_path_or_none()
        if current_row_path is None or current_row_path.parent != path:
            return
        self._current_row_memory[self._path_key(path)] = current_row_path

    def _restore_current_row_for_path(
        self, path: Path, preferred: Path | None = None
    ) -> None:
        candidate = preferred or self._current_row_memory.get(self._path_key(path))
        if candidate is None or candidate.parent != path:
            return
        self._selection_restore_token += 1
        token = self._selection_restore_token
        self._try_restore_current_row(
            candidate,
            token,
            attempts_remaining=self._SELECTION_RESTORE_ATTEMPTS,
        )

    def _try_restore_current_row(
        self,
        candidate: Path,
        token: int,
        *,
        attempts_remaining: int,
    ) -> None:
        if token != self._selection_restore_token:
            return
        if (
            not isValid(self._owner)
            or not isValid(self._model)
            or not isValid(self._view)
        ):
            return

        index = self._model.index_for_path(candidate)
        if index.isValid():
            selection_model = self._view.selectionModel()
            selection_model.setCurrentIndex(
                index,
                QItemSelectionModel.SelectionFlag.Current,
            )
            self._view.scrollTo(index, QAbstractItemView.ScrollHint.PositionAtCenter)
            return

        if attempts_remaining <= 0:
            return
        QTimer.singleShot(
            self._SELECTION_RESTORE_INTERVAL_MS,
            lambda: self._try_restore_current_row(
                candidate,
                token,
                attempts_remaining=attempts_remaining - 1,
            ),
        )

    def _path_key(self, path: Path) -> str:
        return path_key(path)
