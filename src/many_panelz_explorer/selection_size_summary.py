"""Helpers for rendering live selection-size summaries in operation dialogs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from .fast_dir_model import FastDirModel


@dataclass(frozen=True, slots=True)
class SelectionSizeSnapshot:
    """Describe the currently known byte total for one source selection."""

    known_bytes: int
    file_count: int
    directory_count: int
    pending_directory_count: int
    unavailable_directory_count: int
    failed_directory_count: int


def build_selection_size_snapshot(
    *,
    sources: Sequence[Path],
    model: FastDirModel | None,
) -> SelectionSizeSnapshot:
    """Collect current size information for one source list."""

    known_bytes = 0
    file_count = 0
    directory_count = 0
    pending_directory_count = 0
    unavailable_directory_count = 0
    failed_directory_count = 0
    for source in sources:
        candidate = Path(source)
        if candidate.is_file():
            file_count += 1
            try:
                known_bytes += int(candidate.stat(follow_symlinks=False).st_size)
            except OSError:
                continue
            continue
        if not candidate.is_dir():
            continue
        directory_count += 1
        if model is None:
            unavailable_directory_count += 1
            continue
        status = model.folder_size_status(candidate)
        if status == "ready":
            bytes_value = model.folder_size_bytes(candidate)
            known_bytes += int(bytes_value or 0)
            continue
        if status == "calculating":
            pending_directory_count += 1
            continue
        if status == "failed":
            failed_directory_count += 1
            continue
        unavailable_directory_count += 1
    return SelectionSizeSnapshot(
        known_bytes=known_bytes,
        file_count=file_count,
        directory_count=directory_count,
        pending_directory_count=pending_directory_count,
        unavailable_directory_count=unavailable_directory_count,
        failed_directory_count=failed_directory_count,
    )


def build_selection_size_line(
    snapshot: SelectionSizeSnapshot,
    *,
    size_formatter: Callable[[int], str],
) -> str:
    """Render one concise live summary line for the current selection."""

    formatted_known = str(size_formatter(int(snapshot.known_bytes)))
    if (
        snapshot.pending_directory_count <= 0
        and snapshot.unavailable_directory_count <= 0
        and snapshot.failed_directory_count <= 0
    ):
        return f"Selection size: {formatted_known}"
    details: list[str] = []
    if snapshot.pending_directory_count > 0:
        details.append(
            f"calculating {int(snapshot.pending_directory_count)} folder(s)"
        )
    if snapshot.unavailable_directory_count > 0:
        details.append(
            f"{int(snapshot.unavailable_directory_count)} folder size(s) unavailable"
        )
    if snapshot.failed_directory_count > 0:
        details.append(f"{int(snapshot.failed_directory_count)} folder size(s) failed")
    prefix = (
        f"Selection size: {formatted_known} known"
        if snapshot.known_bytes > 0 or snapshot.file_count > 0
        else "Selection size: Calculating..."
    )
    return f"{prefix} ({'; '.join(details)})"
