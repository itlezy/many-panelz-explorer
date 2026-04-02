from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")
pytest.importorskip("pytestqt")

from PySide6.QtCore import QDir, Qt
from PySide6.QtGui import QBrush

from many_panelz_explorer.fast_dir_model import (
    FastDirModel,
    FileListAggregate,
    _DirEntry,
    _FolderSizeState,
)


def _entry(
    path: Path,
    *,
    is_dir: bool,
    modified_ts: float = 0.0,
    is_hidden: bool = False,
    is_system: bool = False,
) -> _DirEntry:
    return _DirEntry(
        path=path,
        name=path.name,
        extension="" if is_dir else path.suffix.lstrip("."),
        is_dir=is_dir,
        size=0 if is_dir else 10,
        modified_ts=modified_ts,
        is_hidden=is_hidden,
        is_system=is_system,
    )


def _load_entries(model: FastDirModel, entries: list[_DirEntry]) -> None:
    model._all_entries = list(entries)
    model._rebuild_visible(reset=True)


def _visible_names(model: FastDirModel) -> list[str]:
    return [
        Path(model.filePath(model.index(row, 0))).name
        for row in range(model.rowCount())
    ]


def test_filter_flags_split_hidden_and_system_entries(tmp_path: Path, qapp) -> None:
    model = FastDirModel()
    model.setFilter(QDir.Filter.AllEntries | QDir.Filter.AllDirs | QDir.Filter.NoDotDot)

    visible = _entry(tmp_path / "visible.txt", is_dir=False)
    hidden = _entry(tmp_path / ".hidden.txt", is_dir=False, is_hidden=True)
    system = _entry(tmp_path / "system.txt", is_dir=False, is_system=True)
    both = _entry(tmp_path / "both.txt", is_dir=False, is_hidden=True, is_system=True)
    _load_entries(model, [visible, hidden, system, both])

    assert _visible_names(model) == ["visible.txt"]

    model.setFilter(
        QDir.Filter.AllEntries
        | QDir.Filter.AllDirs
        | QDir.Filter.NoDotDot
        | QDir.Filter.Hidden
    )
    assert _visible_names(model) == [".hidden.txt", "visible.txt"]

    model.setFilter(
        QDir.Filter.AllEntries
        | QDir.Filter.AllDirs
        | QDir.Filter.NoDotDot
        | QDir.Filter.System
    )
    assert _visible_names(model) == ["system.txt", "visible.txt"]

    model.setFilter(
        QDir.Filter.AllEntries
        | QDir.Filter.AllDirs
        | QDir.Filter.NoDotDot
        | QDir.Filter.Hidden
        | QDir.Filter.System
    )
    assert _visible_names(model) == [
        ".hidden.txt",
        "both.txt",
        "system.txt",
        "visible.txt",
    ]


def test_directory_display_text_can_append_backslash(tmp_path: Path, qapp) -> None:
    model = FastDirModel()
    model.setFilter(QDir.Filter.AllEntries | QDir.Filter.AllDirs | QDir.Filter.NoDotDot)
    _load_entries(model, [_entry(tmp_path / "alpha", is_dir=True)])

    assert model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole) == "[alpha]"

    model.set_append_directory_backslash(True)
    assert model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole) == "[alpha]\\"


def test_directory_display_text_supports_all_bracket_and_backslash_combinations(
    tmp_path: Path, qapp
) -> None:
    model = FastDirModel()
    model.setFilter(QDir.Filter.AllEntries | QDir.Filter.AllDirs | QDir.Filter.NoDotDot)
    _load_entries(model, [_entry(tmp_path / "alpha", is_dir=True)])

    index = model.index(0, 0)
    assert model.data(index, Qt.ItemDataRole.DisplayRole) == "[alpha]"

    model.set_show_square_brackets_around_directories(False)
    assert model.data(index, Qt.ItemDataRole.DisplayRole) == "alpha"

    model.set_append_directory_backslash(True)
    assert model.data(index, Qt.ItemDataRole.DisplayRole) == "alpha\\"

    model.set_show_square_brackets_around_directories(True)
    assert model.data(index, Qt.ItemDataRole.DisplayRole) == "[alpha]\\"


def test_directories_sort_mode_can_force_name_sort_for_non_name_columns(
    tmp_path: Path, qapp
) -> None:
    model = FastDirModel()
    model.setFilter(QDir.Filter.AllEntries | QDir.Filter.AllDirs | QDir.Filter.NoDotDot)
    entries = [
        _entry(tmp_path / "zeta", is_dir=True, modified_ts=10.0),
        _entry(tmp_path / "alpha", is_dir=True, modified_ts=90.0),
        _entry(tmp_path / "mid.txt", is_dir=False, modified_ts=50.0),
    ]
    _load_entries(model, entries)

    model.set_directories_sort_mode("like_files")
    model.sort(3, Qt.SortOrder.AscendingOrder)
    assert _visible_names(model) == ["zeta", "alpha", "mid.txt"]

    model.set_directories_sort_mode("by_name")
    model.sort(3, Qt.SortOrder.AscendingOrder)
    assert _visible_names(model) == ["alpha", "zeta", "mid.txt"]


def test_name_sort_method_controls_numeric_name_order(tmp_path: Path, qapp) -> None:
    model = FastDirModel()
    model.setFilter(QDir.Filter.AllEntries | QDir.Filter.AllDirs | QDir.Filter.NoDotDot)
    entries = [
        _entry(tmp_path / "file10.txt", is_dir=False),
        _entry(tmp_path / "file2.txt", is_dir=False),
        _entry(tmp_path / "File1.txt", is_dir=False),
    ]
    _load_entries(model, entries)

    model.set_name_sort_method("strict_codepoint")
    model.sort(0, Qt.SortOrder.AscendingOrder)
    assert _visible_names(model) == ["File1.txt", "file10.txt", "file2.txt"]

    model.set_name_sort_method("alphabetical_locale")
    model.sort(0, Qt.SortOrder.AscendingOrder)
    assert _visible_names(model) == ["File1.txt", "file10.txt", "file2.txt"]

    model.set_name_sort_method("natural_codepoint")
    model.sort(0, Qt.SortOrder.AscendingOrder)
    assert _visible_names(model) == ["File1.txt", "file2.txt", "file10.txt"]

    model.set_name_sort_method("natural_locale")
    model.sort(0, Qt.SortOrder.AscendingOrder)
    assert _visible_names(model) == ["File1.txt", "file2.txt", "file10.txt"]


def test_non_name_sort_tie_break_uses_selected_name_sort_method(
    tmp_path: Path, qapp
) -> None:
    model = FastDirModel()
    model.setFilter(QDir.Filter.AllEntries | QDir.Filter.AllDirs | QDir.Filter.NoDotDot)
    entries = [
        _entry(tmp_path / "file10.txt", is_dir=False, modified_ts=10.0),
        _entry(tmp_path / "file2.txt", is_dir=False, modified_ts=10.0),
    ]
    _load_entries(model, entries)

    model.set_name_sort_method("strict_codepoint")
    model.sort(3, Qt.SortOrder.AscendingOrder)
    assert _visible_names(model) == ["file10.txt", "file2.txt"]

    model.set_name_sort_method("natural_locale")
    model.sort(3, Qt.SortOrder.AscendingOrder)
    assert _visible_names(model) == ["file2.txt", "file10.txt"]


def test_icon_and_hidden_rendering_roles_follow_preferences(
    tmp_path: Path, qapp
) -> None:
    model = FastDirModel()
    model.setFilter(
        QDir.Filter.AllEntries
        | QDir.Filter.AllDirs
        | QDir.Filter.NoDotDot
        | QDir.Filter.Hidden
    )
    _load_entries(
        model,
        [
            _entry(tmp_path / ".hidden.txt", is_dir=False, is_hidden=True),
            _entry(tmp_path / "visible.txt", is_dir=False),
        ],
    )

    model.set_file_icon_mode("standard_only", dim_hidden_entries=True)
    hidden_index = model.index(0, 0)
    visible_index = model.index(1, 0)

    hidden_icon = model.data(hidden_index, Qt.ItemDataRole.DecorationRole)
    hidden_brush = model.data(hidden_index, Qt.ItemDataRole.ForegroundRole)
    visible_brush = model.data(visible_index, Qt.ItemDataRole.ForegroundRole)

    assert hidden_icon is not None
    assert hidden_icon.isNull() is False
    assert isinstance(hidden_brush, QBrush)
    assert visible_brush is None

    model.set_file_icon_mode("none", dim_hidden_entries=False)
    assert model.data(hidden_index, Qt.ItemDataRole.DecorationRole) is None
    assert model.data(hidden_index, Qt.ItemDataRole.ForegroundRole) is None


def test_visible_summary_reports_file_dir_counts_and_pending_sizes(
    tmp_path: Path, qapp
) -> None:
    model = FastDirModel()
    model.setFilter(QDir.Filter.AllEntries | QDir.Filter.AllDirs | QDir.Filter.NoDotDot)
    ready_dir = _entry(tmp_path / "ready", is_dir=True)
    pending_dir = _entry(tmp_path / "pending", is_dir=True)
    file_entry = _entry(tmp_path / "alpha.txt", is_dir=False)
    _load_entries(model, [ready_dir, pending_dir, file_entry])
    model._folder_size_states[model._path_key(ready_dir.path)] = _FolderSizeState(
        path=ready_dir.path,
        status="ready",
        bytes_value=40,
    )

    assert model.visible_summary() == FileListAggregate(
        entry_count=3,
        file_count=1,
        dir_count=2,
        known_bytes=50,
        pending_dirs=1,
    )


def test_summary_for_paths_deduplicates_paths_and_ignores_missing_entries(
    tmp_path: Path, qapp
) -> None:
    model = FastDirModel()
    model.setFilter(QDir.Filter.AllEntries | QDir.Filter.AllDirs | QDir.Filter.NoDotDot)
    ready_dir = _entry(tmp_path / "ready", is_dir=True)
    file_entry = _entry(tmp_path / "alpha.txt", is_dir=False)
    _load_entries(model, [ready_dir, file_entry])
    model._folder_size_states[model._path_key(ready_dir.path)] = _FolderSizeState(
        path=ready_dir.path,
        status="ready",
        bytes_value=40,
    )

    assert model.summary_for_paths(
        [file_entry.path, ready_dir.path, file_entry.path, tmp_path / "missing.txt"]
    ) == FileListAggregate(
        entry_count=2,
        file_count=1,
        dir_count=1,
        known_bytes=50,
        pending_dirs=0,
    )
