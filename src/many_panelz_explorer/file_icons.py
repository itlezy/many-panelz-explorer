"""Shared file and root icon helpers used across the explorer UI."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QFileInfo
from PySide6.QtWidgets import QApplication, QFileIconProvider, QStyle

if TYPE_CHECKING:
    from PySide6.QtGui import QIcon

FILE_ICON_MODE_ALL_ASSOCIATED = "all_associated"
FILE_ICON_MODE_STANDARD_ONLY = "standard_only"
FILE_ICON_MODE_NONE = "none"

ALLOWED_FILE_ICON_MODES = {
    FILE_ICON_MODE_ALL_ASSOCIATED,
    FILE_ICON_MODE_STANDARD_ONLY,
    FILE_ICON_MODE_NONE,
}


def _is_drive_root(path: Path) -> bool:
    anchor = path.anchor
    return bool(anchor) and path == Path(anchor)


class FileIconResolver:
    """Resolve file and directory icons with lightweight caching."""

    def __init__(self) -> None:
        self._provider = QFileIconProvider()
        self._associated_icon_cache: dict[tuple[str, bool], QIcon] = {}
        self._standard_file_icon_cache: QIcon | None = None
        self._standard_dir_icon_cache: QIcon | None = None
        self._standard_drive_icon_cache: QIcon | None = None

    def icon_for_path(self, path: Path, *, is_dir: bool, mode: str) -> QIcon | None:
        """Return the preferred icon for one file-system path."""

        normalized_mode = str(mode).strip().lower()
        if normalized_mode == FILE_ICON_MODE_NONE:
            return None
        if normalized_mode == FILE_ICON_MODE_STANDARD_ONLY:
            return self._standard_icon(is_dir=is_dir, is_drive=_is_drive_root(path))

        cache_key = (str(path), bool(is_dir))
        cached_icon = self._associated_icon_cache.get(cache_key)
        if cached_icon is not None:
            return cached_icon

        icon = self._provider.icon(QFileInfo(str(path)))
        if icon.isNull():
            icon = self._standard_icon(is_dir=is_dir, is_drive=_is_drive_root(path))
        self._associated_icon_cache[cache_key] = icon
        return icon

    def _standard_icon(self, *, is_dir: bool, is_drive: bool) -> QIcon:
        style = QApplication.style()

        if is_drive:
            if self._standard_drive_icon_cache is None:
                self._standard_drive_icon_cache = style.standardIcon(
                    QStyle.StandardPixmap.SP_DriveHDIcon
                )
            return self._standard_drive_icon_cache

        if is_dir:
            if self._standard_dir_icon_cache is None:
                self._standard_dir_icon_cache = style.standardIcon(
                    QStyle.StandardPixmap.SP_DirIcon
                )
            return self._standard_dir_icon_cache

        if self._standard_file_icon_cache is None:
            self._standard_file_icon_cache = style.standardIcon(
                QStyle.StandardPixmap.SP_FileIcon
            )
        return self._standard_file_icon_cache


_shared_file_icon_resolver_instance: FileIconResolver | None = None


def shared_file_icon_resolver() -> FileIconResolver:
    """Return the process-wide icon resolver instance."""

    global _shared_file_icon_resolver_instance
    if _shared_file_icon_resolver_instance is None:
        _shared_file_icon_resolver_instance = FileIconResolver()
    return _shared_file_icon_resolver_instance
