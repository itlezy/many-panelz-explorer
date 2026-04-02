"""Asynchronous directory listing model for explorer tabs."""

from __future__ import annotations

import fnmatch
import os
import re
import weakref
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from functools import cmp_to_key
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

from PySide6.QtCore import (
    QAbstractTableModel,
    QCollator,
    QDir,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
    Signal,
)
from PySide6.QtGui import QBrush, QColor
from threep_commons.fs_paths import path_key

from .file_icons import (
    ALLOWED_FILE_ICON_MODES,
    FILE_ICON_MODE_NONE,
    shared_file_icon_resolver,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from .folder_sizes import FolderSizeCalculator

_HIDDEN_ATTRIBUTE_MASK = 0x2
_SYSTEM_ATTRIBUTE_MASK = 0x4
_NAME_SORT_METHOD_STRICT_CODEPOINT = "strict_codepoint"
_NAME_SORT_METHOD_NATURAL_CODEPOINT = "natural_codepoint"
_NAME_SORT_METHOD_ALPHABETICAL_LOCALE = "alphabetical_locale"
_NAME_SORT_METHOD_NATURAL_LOCALE = "natural_locale"
_ALLOWED_NAME_SORT_METHODS = {
    _NAME_SORT_METHOD_ALPHABETICAL_LOCALE,
    _NAME_SORT_METHOD_STRICT_CODEPOINT,
    _NAME_SORT_METHOD_NATURAL_CODEPOINT,
    _NAME_SORT_METHOD_NATURAL_LOCALE,
}


@dataclass(slots=True)
class _DirEntry:
    path: Path
    name: str
    extension: str
    is_dir: bool
    size: int
    modified_ts: float
    is_hidden: bool
    is_system: bool


@dataclass(slots=True, frozen=True)
class _FolderSizeState:
    path: Path
    status: Literal["calculating", "ready", "failed"]
    bytes_value: int = 0


def _scan_directory(path: Path) -> list[_DirEntry]:
    entries: list[_DirEntry] = []
    with os.scandir(path) as iterator:
        for item in iterator:
            item_path = Path(item.path)
            try:
                item_stat = item.stat(follow_symlinks=False)
            except OSError:
                continue

            try:
                is_dir = item.is_dir(follow_symlinks=False)
            except OSError:
                is_dir = False

            name = item.name
            extension = "" if is_dir else item_path.suffix.lstrip(".")
            size = 0 if is_dir else int(item_stat.st_size)
            hidden = name.startswith(".")
            system = False

            if os.name == "nt":
                attributes = int(getattr(item_stat, "st_file_attributes", 0))
                hidden = hidden or bool(attributes & _HIDDEN_ATTRIBUTE_MASK)
                system = bool(attributes & _SYSTEM_ATTRIBUTE_MASK)

            entries.append(
                _DirEntry(
                    path=item_path,
                    name=name,
                    extension=extension,
                    is_dir=is_dir,
                    size=size,
                    modified_ts=float(item_stat.st_mtime),
                    is_hidden=hidden,
                    is_system=system,
                )
            )
    return entries


class _ModelSignals(QObject):
    listing_ready = Signal(int, str, object, object)
    folder_size_ready = Signal(int, str, object, object)


class FastDirModel(QAbstractTableModel):
    """Present filesystem entries in a table model with async refresh."""

    directory_loaded = Signal(str)
    folder_size_state_changed = Signal(str, str, int)

    _HEADERS = ("Name", "Ext", "Size", "Date")
    _executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="mpe-dir-scan")

    def __init__(
        self,
        parent: QObject | None = None,
        *,
        size_formatter: Callable[[int], str] | None = None,
    ) -> None:
        super().__init__(parent)
        self._current_path = Path.home()
        self._filter_flags = (
            QDir.Filter.AllEntries | QDir.Filter.AllDirs | QDir.Filter.NoDot
        )
        self._name_filters: list[str] = []
        self._name_filter_disables = True
        self._all_entries: list[_DirEntry] = []
        self._visible_entries: list[_DirEntry] = []
        self._show_parent_entry = True
        self._show_hidden = False
        self._show_system = False
        self._sort_column = 0
        self._sort_order = Qt.SortOrder.AscendingOrder
        self._directories_sort_mode = "like_files"
        self._show_parent_dir_at_drive_root = True
        self._show_square_brackets_around_directories = True
        self._append_directory_backslash = False
        self._name_sort_method = _NAME_SORT_METHOD_NATURAL_LOCALE
        self._file_icon_mode = "all_associated"
        self._dim_hidden_entries = True
        self._request_id = 0
        self._size_formatter = size_formatter or self._default_size_formatter
        self._folder_size_states: dict[str, _FolderSizeState] = {}
        self._alphabetical_collator = QCollator()
        self._alphabetical_collator.setCaseSensitivity(
            Qt.CaseSensitivity.CaseInsensitive
        )
        self._alphabetical_collator.setNumericMode(False)
        self._natural_collator = QCollator()
        self._natural_collator.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._natural_collator.setNumericMode(True)
        self._signals = _ModelSignals(self)
        self._signals.listing_ready.connect(self._on_listing_ready)
        self._signals.folder_size_ready.connect(self._on_folder_size_ready)
        self._refresh_filter_flags()

    def rowCount(
        self,
        parent: QModelIndex | QPersistentModelIndex | None = None,
    ) -> int:
        if parent is None:
            parent = QModelIndex()
        if parent.isValid():
            return 0
        return len(self._visible_entries) + (1 if self._show_parent_entry else 0)

    def columnCount(
        self,
        parent: QModelIndex | QPersistentModelIndex | None = None,
    ) -> int:
        if parent is None:
            parent = QModelIndex()
        if parent.isValid():
            return 0
        return len(self._HEADERS)

    def index(
        self,
        row: int | str,
        column: int = 0,
        parent: QModelIndex | QPersistentModelIndex | None = None,
    ) -> QModelIndex:
        if parent is None:
            parent = QModelIndex()
        if isinstance(row, str):
            return self.index_for_path(Path(row))
        if parent.isValid() or row < 0 or column < 0:
            return QModelIndex()
        if row >= self.rowCount() or column >= self.columnCount():
            return QModelIndex()
        return self.createIndex(int(row), int(column), None)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = int(Qt.ItemDataRole.DisplayRole),
    ) -> object:
        if not index.isValid():
            return None

        if role == int(Qt.ItemDataRole.TextAlignmentRole) and index.column() == 2:
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        if role == int(Qt.ItemDataRole.UserRole):
            return self.filePath(index)

        if role == int(Qt.ItemDataRole.DecorationRole) and index.column() == 0:
            if self._is_parent_row(index.row()):
                return None
            entry = self._entry_for_row(index.row())
            if entry is None:
                return None
            return shared_file_icon_resolver().icon_for_path(
                entry.path,
                is_dir=entry.is_dir,
                mode=self._file_icon_mode,
            )

        if role == int(Qt.ItemDataRole.ForegroundRole):
            if self._is_parent_row(index.row()):
                return None
            entry = self._entry_for_row(index.row())
            if entry is None:
                return None
            if self._dim_hidden_entries and (entry.is_hidden or entry.is_system):
                return QBrush(QColor("#7A7A7A"))
            return None

        if role != int(Qt.ItemDataRole.DisplayRole):
            return None

        row = index.row()
        col = index.column()

        if self._is_parent_row(row):
            return ".." if col == 0 else ""

        entry = self._entry_for_row(row)
        if entry is None:
            return ""

        if col == 0:
            if not entry.is_dir:
                return entry.name
            return self._format_directory_name(entry)
        if col == 1:
            return "" if entry.is_dir else entry.extension
        if col == 2:
            return (
                self._format_directory_size(entry)
                if entry.is_dir
                else self._format_size(entry.size)
            )
        if col == 3:
            return datetime.fromtimestamp(entry.modified_ts).strftime("%Y-%m-%d %H:%M")
        return ""

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = int(Qt.ItemDataRole.DisplayRole),
    ) -> object:
        if (
            orientation == Qt.Orientation.Horizontal
            and role == int(Qt.ItemDataRole.DisplayRole)
            and 0 <= section < len(self._HEADERS)
        ):
            return self._HEADERS[section]
        return super().headerData(section, orientation, role)

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def setReadOnly(self, _read_only: bool) -> None:
        # Compatibility no-op: ExplorerTab expects QFileSystemModel-style API.
        return

    def setRootPath(self, path: str) -> QModelIndex:
        target = Path(path).expanduser()
        if not target.exists() or not target.is_dir():
            target = Path.home()
        self._current_path = target

        self._request_id += 1
        request_id = self._request_id

        self.beginResetModel()
        self._all_entries = []
        self._visible_entries = []
        self._folder_size_states = {}
        self.endResetModel()

        model_ref = weakref.ref(self)

        def _done_callback(future: Future[list[_DirEntry]]) -> None:
            model = model_ref()
            if model is None:
                return
            try:
                listing = future.result()
                error: str | None = None
            except Exception as exc:  # pragma: no cover - defensive
                listing = []
                error = str(exc)
            model._signals.listing_ready.emit(
                request_id, str(target), list(listing), error
            )

        future = self._executor.submit(_scan_directory, target)
        future.add_done_callback(_done_callback)
        return QModelIndex()

    def filePath(self, index: QModelIndex | QPersistentModelIndex) -> str:
        if not index.isValid():
            return ""
        row = index.row()
        if self._is_parent_row(row):
            if self.parent_row_opens_root_picker():
                return ""
            return str(self._current_path.parent)
        entry = self._entry_for_row(row)
        return str(entry.path) if entry is not None else ""

    def index_for_path(self, path: Path) -> QModelIndex:
        target = self._path_key(path)
        if (
            self._show_parent_entry
            and not self.parent_row_opens_root_picker()
            and self._path_key(self._current_path.parent) == target
        ):
            return self.index(0, 0)
        offset = 1 if self._show_parent_entry else 0
        for idx, entry in enumerate(self._visible_entries):
            if self._path_key(entry.path) == target:
                return self.index(idx + offset, 0)
        return QModelIndex()

    def is_parent_index(self, index: QModelIndex) -> bool:
        return index.isValid() and self._is_parent_row(index.row())

    def setFilter(self, flags: object) -> None:
        self._filter_flags = self._coerce_filter_flags(flags)
        self._refresh_filter_flags()
        self._rebuild_visible(reset=True)

    def filter(self) -> QDir.Filter:
        return self._filter_flags

    def setNameFilters(self, filters: list[str]) -> None:
        self._name_filters = [str(pattern) for pattern in filters]
        self._rebuild_visible(reset=True)

    def nameFilters(self) -> list[str]:
        return list(self._name_filters)

    def setNameFilterDisables(self, disables: bool) -> None:
        self._name_filter_disables = bool(disables)
        self._rebuild_visible(reset=True)

    def nameFilterDisables(self) -> bool:
        return self._name_filter_disables

    def sort(
        self,
        column: int,
        order: Qt.SortOrder = Qt.SortOrder.AscendingOrder,
    ) -> None:
        self._sort_column = max(0, min(int(column), len(self._HEADERS) - 1))
        self._sort_order = order
        self._rebuild_visible(reset=True)

    def set_size_formatter(self, formatter: Callable[[int], str] | None) -> None:
        self._size_formatter = formatter or self._default_size_formatter
        row_count = self.rowCount()
        if row_count <= 0:
            return
        top = self.index(0, 2)
        bottom = self.index(row_count - 1, 2)
        if top.isValid() and bottom.isValid():
            self.dataChanged.emit(
                top,
                bottom,
                [int(Qt.ItemDataRole.DisplayRole)],
            )

    def set_directories_sort_mode(self, mode: str) -> None:
        """Apply the configured directory sorting behavior."""

        normalized_mode = str(mode).strip().lower()
        self._directories_sort_mode = (
            "by_name" if normalized_mode == "by_name" else "like_files"
        )
        self._rebuild_visible(reset=True)

    def set_show_parent_dir_at_drive_root(self, enabled: bool) -> None:
        """Configure whether drive roots should expose a synthetic parent row."""

        self._show_parent_dir_at_drive_root = bool(enabled)

    def set_show_square_brackets_around_directories(self, enabled: bool) -> None:
        """Apply directory square-bracket formatting preferences."""

        self._show_square_brackets_around_directories = bool(enabled)
        self._emit_name_column_changed()

    def set_append_directory_backslash(self, enabled: bool) -> None:
        """Apply directory text formatting preferences."""

        self._append_directory_backslash = bool(enabled)
        self._emit_name_column_changed()

    def set_name_sort_method(self, mode: str) -> None:
        """Apply the configured file-name comparison method."""

        normalized_mode = str(mode).strip().lower()
        if normalized_mode not in _ALLOWED_NAME_SORT_METHODS:
            normalized_mode = _NAME_SORT_METHOD_NATURAL_LOCALE
        self._name_sort_method = normalized_mode
        self._rebuild_visible(reset=True)

    def set_file_icon_mode(self, mode: str, *, dim_hidden_entries: bool) -> None:
        """Apply file icon and hidden-entry display preferences."""

        normalized_mode = str(mode).strip().lower()
        if normalized_mode not in ALLOWED_FILE_ICON_MODES:
            normalized_mode = FILE_ICON_MODE_NONE
        self._file_icon_mode = normalized_mode
        self._dim_hidden_entries = bool(dim_hidden_entries)
        row_count = self.rowCount()
        if row_count <= 0:
            return
        top = self.index(0, 0)
        bottom = self.index(row_count - 1, 0)
        if top.isValid() and bottom.isValid():
            self.dataChanged.emit(
                top,
                bottom,
                [
                    int(Qt.ItemDataRole.DecorationRole),
                    int(Qt.ItemDataRole.ForegroundRole),
                ],
            )

    def request_folder_sizes(
        self,
        paths: Sequence[Path],
        *,
        calculator: FolderSizeCalculator,
    ) -> int:
        """Queue one folder-size calculation batch for current visible rows.

        Args:
            paths: Folder paths that should be calculated.
            calculator: Folder-size backend chosen for this request batch.

        Returns:
            Number of newly queued folder calculations.
        """

        queued = 0
        generation = self._request_id
        current_root_key = self._path_key(self._current_path)
        unique_paths: dict[str, Path] = {}
        for path in paths:
            candidate = Path(path)
            if (
                not candidate.is_dir()
                or self._path_key(candidate.parent) != current_root_key
            ):
                continue
            unique_paths[self._path_key(candidate)] = candidate
        for folder_key, folder_path in unique_paths.items():
            existing_state = self._folder_size_states.get(folder_key)
            if existing_state is not None and existing_state.status in {
                "calculating",
                "ready",
            }:
                continue
            self._folder_size_states[folder_key] = _FolderSizeState(
                path=folder_path,
                status="calculating",
            )
            self.folder_size_state_changed.emit(
                str(folder_path),
                "calculating",
                0,
            )
            self._emit_size_changed_for_path(folder_path)
            queued += 1
            future = self._executor.submit(calculator.calculate, folder_path)
            future.add_done_callback(
                self._folder_size_done_callback(
                    request_id=generation,
                    folder_path=folder_path,
                )
            )
        return queued

    def visible_directory_paths(self) -> list[Path]:
        """Return all currently visible directory rows in display order."""

        return [entry.path for entry in self._visible_entries if entry.is_dir]

    def visible_paths(self) -> list[Path]:
        """Return all currently visible real paths in display order."""

        return [entry.path for entry in self._visible_entries]

    def visible_entry_count(self) -> int:
        """Return the number of visible real filesystem entries."""

        return len(self._visible_entries)

    def visible_summary(self) -> tuple[int, int, int]:
        """Return `(count, known_bytes, pending_dirs)` for visible entries."""

        return self._summary_for_entries(self._visible_entries)

    def summary_for_paths(self, paths: Sequence[Path]) -> tuple[int, int, int]:
        """Return `(count, known_bytes, pending_dirs)` for visible matching paths."""

        entries_by_key = {
            self._path_key(entry.path): entry for entry in self._visible_entries
        }
        matched_entries: list[_DirEntry] = []
        seen_keys: set[str] = set()
        for path in paths:
            entry_key = self._path_key(Path(path))
            if entry_key in seen_keys:
                continue
            seen_keys.add(entry_key)
            entry = entries_by_key.get(entry_key)
            if entry is not None:
                matched_entries.append(entry)
        return self._summary_for_entries(matched_entries)

    def folder_size_status(
        self,
        path: Path,
    ) -> Literal["idle", "calculating", "ready", "failed"]:
        """Return the current folder-size state for one visible directory path."""

        state = self._folder_size_states.get(self._path_key(Path(path)))
        if state is None:
            return "idle"
        return state.status

    def folder_size_bytes(self, path: Path) -> int | None:
        """Return cached directory bytes when the size has completed."""

        state = self._folder_size_states.get(self._path_key(Path(path)))
        if state is None or state.status != "ready":
            return None
        return int(state.bytes_value)

    def format_size_value(self, value: int) -> str:
        """Format one byte value using the model's active size formatter."""

        return self._format_size(int(value))

    def _on_listing_ready(
        self,
        request_id: int,
        path: str,
        entries: object,
        error: object,
    ) -> None:
        if request_id != self._request_id:
            return
        if self._path_key(Path(path)) != self._path_key(self._current_path):
            return
        if error is not None:
            parsed_entries: list[_DirEntry] = []
        else:
            parsed_entries = cast("list[_DirEntry]", entries)

        self.beginResetModel()
        self._all_entries = parsed_entries
        self._visible_entries = self._sort_entries(
            self._apply_entry_filters(parsed_entries)
        )
        self.endResetModel()
        self.directory_loaded.emit(str(self._current_path))

    def _on_folder_size_ready(
        self,
        request_id: int,
        path: str,
        bytes_value: object,
        error: object,
    ) -> None:
        if request_id != self._request_id:
            return
        folder_path = Path(path)
        folder_key = self._path_key(folder_path)
        if self._path_key(folder_path.parent) != self._path_key(self._current_path):
            return
        if error is None:
            self._folder_size_states[folder_key] = _FolderSizeState(
                path=folder_path,
                status="ready",
                bytes_value=int(cast("int", bytes_value)),
            )
            self.folder_size_state_changed.emit(
                str(folder_path),
                "ready",
                int(cast("int", bytes_value)),
            )
        else:
            self._folder_size_states[folder_key] = _FolderSizeState(
                path=folder_path,
                status="failed",
            )
            self.folder_size_state_changed.emit(
                str(folder_path),
                "failed",
                0,
            )
        if self._sort_column == 2:
            self._rebuild_visible(reset=True)
        self._emit_size_changed_for_path(folder_path)

    def _refresh_filter_flags(self) -> None:
        self._show_hidden = bool(self._filter_flags & QDir.Filter.Hidden)
        self._show_system = bool(self._filter_flags & QDir.Filter.System)
        self._show_parent_entry = not bool(self._filter_flags & QDir.Filter.NoDotDot)

    def _apply_entry_filters(self, entries: list[_DirEntry]) -> list[_DirEntry]:
        filtered: list[_DirEntry] = []
        for entry in entries:
            if not self._show_hidden and entry.is_hidden:
                continue
            if not self._show_system and entry.is_system:
                continue
            if not self._matches_name_filters(entry):
                continue
            filtered.append(entry)
        return filtered

    def _matches_name_filters(self, entry: _DirEntry) -> bool:
        if self._name_filter_disables or not self._name_filters:
            return True
        candidate = entry.name.casefold()
        for pattern in self._name_filters:
            if fnmatch.fnmatch(candidate, str(pattern).casefold()):
                return True
        return False

    def _sort_entries(self, entries: list[_DirEntry]) -> list[_DirEntry]:
        return sorted(entries, key=cmp_to_key(self._compare_entries))

    def _rebuild_visible(self, *, reset: bool) -> None:
        if reset:
            self.beginResetModel()
        self._visible_entries = self._sort_entries(
            self._apply_entry_filters(self._all_entries)
        )
        if reset:
            self.endResetModel()

    def _is_parent_row(self, row: int) -> bool:
        return self._show_parent_entry and row == 0

    def _entry_for_row(self, row: int) -> _DirEntry | None:
        offset = 1 if self._show_parent_entry else 0
        idx = row - offset
        if idx < 0 or idx >= len(self._visible_entries):
            return None
        return self._visible_entries[idx]

    def parent_row_opens_root_picker(self) -> bool:
        """Return whether the visible parent row represents the root picker."""

        return self._show_parent_entry and self._is_drive_root(self._current_path)

    def _format_size(self, value: int) -> str:
        try:
            return str(self._size_formatter(int(value)))
        except Exception:  # pragma: no cover - defensive
            return self._default_size_formatter(int(value))

    def _format_directory_size(self, entry: _DirEntry) -> str:
        state = self._folder_size_states.get(self._path_key(entry.path))
        if state is None:
            return ""
        if state.status == "calculating":
            return "Calculating..."
        if state.status == "failed":
            return "Error"
        return self._format_size(state.bytes_value)

    def _coerce_filter_flags(self, flags: object) -> QDir.Filter:
        if isinstance(flags, QDir.Filter):
            return flags
        return cast("QDir.Filter", flags)

    def _compare_entries(self, left: _DirEntry, right: _DirEntry) -> int:
        dir_cmp = self._compare_dir_group(left, right)
        name_cmp = self._compare_names(left.name, right.name)

        if self._sort_column == 0:
            if dir_cmp != 0:
                return dir_cmp
            return self._apply_sort_order(name_cmp)

        if dir_cmp != 0:
            return dir_cmp

        if self._directories_sort_mode == "by_name" and left.is_dir and right.is_dir:
            return self._apply_sort_order(name_cmp)

        if self._sort_column == 1:
            value_cmp = self._compare_text_values(left.extension, right.extension)
        elif self._sort_column == 2:
            value_cmp = self._compare_numeric_values(
                self._sortable_size_value(left),
                self._sortable_size_value(right),
            )
        else:
            value_cmp = self._compare_numeric_values(
                left.modified_ts,
                right.modified_ts,
            )
        if value_cmp != 0:
            return self._apply_sort_order(value_cmp)
        if dir_cmp != 0:
            return dir_cmp
        return self._apply_sort_order(name_cmp)

    def _compare_dir_group(self, left: _DirEntry, right: _DirEntry) -> int:
        if left.is_dir == right.is_dir:
            return 0
        return -1 if left.is_dir else 1

    def _compare_numeric_values(self, left: float | int, right: float | int) -> int:
        if left < right:
            return -1
        if left > right:
            return 1
        return 0

    def _compare_text_values(self, left: str, right: str) -> int:
        return self._compare_names(left, right)

    def _compare_names(self, left: str, right: str) -> int:
        if self._name_sort_method == _NAME_SORT_METHOD_STRICT_CODEPOINT:
            return self._compare_codepoint_names(left, right, natural=False)
        if self._name_sort_method == _NAME_SORT_METHOD_NATURAL_CODEPOINT:
            return self._compare_codepoint_names(left, right, natural=True)
        if self._name_sort_method == _NAME_SORT_METHOD_ALPHABETICAL_LOCALE:
            return self._compare_locale_names(left, right, natural=False)
        return self._compare_locale_names(left, right, natural=True)

    def _compare_locale_names(self, left: str, right: str, *, natural: bool) -> int:
        collator = self._natural_collator if natural else self._alphabetical_collator
        result = int(collator.compare(left, right))
        if result != 0:
            return result
        return self._compare_codepoint_names(left, right, natural=natural)

    def _compare_codepoint_names(self, left: str, right: str, *, natural: bool) -> int:
        if natural:
            left_key = self._natural_codepoint_key(left)
            right_key = self._natural_codepoint_key(right)
        else:
            left_key = self._strict_codepoint_key(left)
            right_key = self._strict_codepoint_key(right)
        if left_key < right_key:
            return -1
        if left_key > right_key:
            return 1
        return 0

    def _strict_codepoint_key(self, value: str) -> tuple[str, str]:
        return value.upper(), value

    def _natural_codepoint_key(
        self, value: str
    ) -> tuple[tuple[int, object, object], ...]:
        parts = re.split(r"(\d+)", value)
        key: list[tuple[int, object, object]] = []
        for part in parts:
            if not part:
                continue
            if part.isdigit():
                key.append((0, int(part), len(part)))
                continue
            key.append((1, part.casefold(), part))
        return tuple(key)

    def _sortable_size_value(self, item: _DirEntry) -> int:
        if not item.is_dir:
            return int(item.size)
        folder_state = self._folder_size_states.get(self._path_key(item.path))
        if folder_state is None:
            return -1
        return int(folder_state.bytes_value)

    def _apply_sort_order(self, comparison: int) -> int:
        if self._sort_order == Qt.SortOrder.DescendingOrder:
            return -comparison
        return comparison

    def _format_directory_name(self, entry: _DirEntry) -> str:
        name = entry.name
        if self._show_square_brackets_around_directories:
            name = f"[{name}]"
        if self._append_directory_backslash:
            name = f"{name}\\"
        return name

    def _emit_name_column_changed(self) -> None:
        row_count = self.rowCount()
        if row_count <= 0:
            return
        top = self.index(0, 0)
        bottom = self.index(row_count - 1, 0)
        if top.isValid() and bottom.isValid():
            self.dataChanged.emit(
                top,
                bottom,
                [int(Qt.ItemDataRole.DisplayRole)],
            )

    def _is_drive_root(self, path: Path) -> bool:
        if not self._show_parent_dir_at_drive_root:
            return False
        if os.name != "nt":
            return False
        normalized_path = Path(path)
        anchor = normalized_path.anchor
        return bool(anchor) and normalized_path == Path(anchor)

    def _default_size_formatter(self, value: int) -> str:
        return f"{int(value):,}"

    def _path_key(self, path: Path) -> str:
        return path_key(path)

    def _summary_for_entries(
        self, entries: Sequence[_DirEntry]
    ) -> tuple[int, int, int]:
        """Return `(count, known_bytes, pending_dirs)` for directory entries."""

        count = 0
        known_bytes = 0
        pending_dirs = 0
        for entry in entries:
            count += 1
            if not entry.is_dir:
                known_bytes += int(entry.size)
                continue
            folder_state = self._folder_size_states.get(self._path_key(entry.path))
            if folder_state is not None and folder_state.status == "ready":
                known_bytes += int(folder_state.bytes_value)
                continue
            pending_dirs += 1
        return count, known_bytes, pending_dirs

    def _emit_size_changed_for_path(self, path: Path) -> None:
        index = self.index_for_path(path)
        if not index.isValid():
            return
        size_index = index.siblingAtColumn(2)
        self.dataChanged.emit(
            size_index,
            size_index,
            [int(Qt.ItemDataRole.DisplayRole)],
        )

    def _folder_size_done_callback(
        self,
        *,
        request_id: int,
        folder_path: Path,
    ) -> Callable[[Future[int]], None]:
        model_ref = weakref.ref(self)

        def _done_callback(future: Future[int]) -> None:
            model = model_ref()
            if model is None:
                return
            try:
                result = int(future.result())
                error: str | None = None
            except Exception as exc:  # pragma: no cover - defensive
                result = 0
                error = str(exc)
            model._signals.folder_size_ready.emit(
                request_id,
                str(folder_path),
                result,
                error,
            )

        return _done_callback
