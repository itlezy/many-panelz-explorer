"""Editable TOML-backed bookmark storage with folder-tree support."""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, TypeGuard, cast

from threep_commons.fs_paths import normalize_windows_path_text, path_key


class _SettingsPathProvider(Protocol):
    """Describe the settings object shape needed to derive the bookmarks file."""

    settings_path: Path | str


@dataclass(frozen=True, slots=True)
class Bookmark:
    """Represent one named bookmark target."""

    label: str
    path: Path
    folder: str = ""


@dataclass(frozen=True, slots=True)
class BookmarkFolder:
    """Represent one explicit bookmark folder entry."""

    path: str


@dataclass(frozen=True, slots=True)
class BookmarkCollection:
    """Represent the persisted folder and bookmark payload."""

    folders: tuple[BookmarkFolder, ...] = ()
    bookmarks: tuple[Bookmark, ...] = ()


@dataclass(slots=True)
class BookmarkFolderNode:
    """Represent one runtime bookmark-tree folder node."""

    path: str
    folders: list[BookmarkFolderNode] = field(default_factory=list)
    bookmarks: list[Bookmark] = field(default_factory=list)

    @property
    def label(self) -> str:
        """Return the display label for this folder node."""

        if not self.path:
            return ""
        return bookmark_folder_label(self.path)


class BookmarkStore:
    """Load and save bookmarks from an editable TOML file."""

    def __init__(self, bookmarks_file: Path) -> None:
        self._bookmarks_file = Path(bookmarks_file)

    @classmethod
    def from_settings(cls, settings: _SettingsPathProvider) -> BookmarkStore:
        """Build a store rooted beside the app INI settings file."""

        settings_path = Path(str(settings.settings_path))
        return cls(settings_path.with_suffix(".bookmarks.toml"))

    @property
    def bookmarks_file(self) -> Path:
        """Return the on-disk TOML file that stores bookmarks."""

        return Path(self._bookmarks_file)

    def load(self) -> BookmarkCollection:
        """Load bookmark folders and leaves from disk."""

        if not self._bookmarks_file.exists():
            return BookmarkCollection()
        try:
            raw_text = self._bookmarks_file.read_text(encoding="utf-8")
            raw_payload = tomllib.loads(raw_text)
        except tomllib.TOMLDecodeError as exc:
            raise RuntimeError(f"Could not parse bookmarks file: {exc}") from exc

        folders = _parse_folders(raw_payload.get("folders", []))
        bookmarks = _parse_bookmarks(raw_payload.get("bookmarks", []))
        return BookmarkCollection(
            folders=tuple(folders),
            bookmarks=tuple(bookmarks),
        )

    def ensure_file_exists(self) -> Path:
        """Create an empty bookmarks file when it does not already exist."""

        self._bookmarks_file.parent.mkdir(parents=True, exist_ok=True)
        if not self._bookmarks_file.exists():
            self._bookmarks_file.write_text("", encoding="utf-8")
        return Path(self._bookmarks_file)

    def save(self, collection: BookmarkCollection) -> Path:
        """Persist folders and bookmarks using the canonical TOML layout."""

        self._bookmarks_file.parent.mkdir(parents=True, exist_ok=True)
        self._bookmarks_file.write_text(
            _serialize_collection(collection),
            encoding="utf-8",
        )
        return Path(self._bookmarks_file)

    def add_or_update(
        self,
        *,
        path: Path,
        label: str,
        folder: str = "",
    ) -> BookmarkCollection:
        """Add a bookmark, or update the existing bookmark for one filesystem path."""

        current = self.load()
        target_path = Path(path)
        target_key = path_key(target_path)
        target_folder = normalize_bookmark_folder_path(folder)
        next_bookmarks: list[Bookmark] = []
        replaced = False
        for bookmark in current.bookmarks:
            if path_key(bookmark.path) == target_key:
                if not replaced:
                    next_bookmarks.append(
                        Bookmark(label=label, path=target_path, folder=target_folder)
                    )
                    replaced = True
                continue
            next_bookmarks.append(bookmark)
        if not replaced:
            next_bookmarks.append(
                Bookmark(label=label, path=target_path, folder=target_folder)
            )
        updated = BookmarkCollection(
            folders=current.folders,
            bookmarks=tuple(next_bookmarks),
        )
        self.save(updated)
        return updated

    def remove(self, *, path: Path) -> BookmarkCollection:
        """Remove the bookmark leaf for one filesystem path when it exists."""

        current = self.load()
        target_key = path_key(Path(path))
        next_bookmarks = tuple(
            bookmark
            for bookmark in current.bookmarks
            if path_key(bookmark.path) != target_key
        )
        updated = BookmarkCollection(
            folders=current.folders,
            bookmarks=next_bookmarks,
        )
        self.save(updated)
        return updated

    def create_folder(self, folder_path: str) -> BookmarkCollection:
        """Create one explicit bookmark folder path when missing."""

        current = self.load()
        normalized = normalize_bookmark_folder_path(folder_path)
        if not normalized:
            return current
        existing = {folder.path for folder in current.folders}
        if normalized in existing:
            return current
        updated = BookmarkCollection(
            folders=(*current.folders, BookmarkFolder(path=normalized)),
            bookmarks=current.bookmarks,
        )
        self.save(updated)
        return updated


def default_bookmark_label(path: Path) -> str:
    """Return the default label shown when prompting to add one bookmark."""

    bookmark_path = Path(path)
    if bookmark_path.name:
        return bookmark_path.name
    return str(bookmark_path)


def normalize_bookmark_folder_path(value: str) -> str:
    """Normalize one logical bookmark-folder path."""

    raw_text = str(value or "").strip().replace("\\", "/")
    parts = [segment.strip() for segment in raw_text.split("/") if segment.strip()]
    return "/".join(parts)


def bookmark_folder_label(folder_path: str) -> str:
    """Return the display label for one logical bookmark-folder path."""

    normalized = normalize_bookmark_folder_path(folder_path)
    if not normalized:
        return ""
    return normalized.rsplit("/", 1)[-1]


def collect_folder_paths(collection: BookmarkCollection) -> tuple[str, ...]:
    """Return all folder paths used explicitly or by bookmark placement."""

    ordered_paths: list[str] = []
    seen_paths: set[str] = set()
    for folder in collection.folders:
        _append_folder_path_with_parents(
            ordered_paths,
            seen_paths,
            folder.path,
        )
    for bookmark in collection.bookmarks:
        if bookmark.folder:
            _append_folder_path_with_parents(
                ordered_paths,
                seen_paths,
                bookmark.folder,
            )
    return tuple(ordered_paths)


def build_bookmark_tree(collection: BookmarkCollection) -> BookmarkFolderNode:
    """Build the runtime bookmark tree from a folder-aware collection."""

    root = BookmarkFolderNode(path="")
    nodes: dict[str, BookmarkFolderNode] = {"": root}

    for folder_path in collect_folder_paths(collection):
        parent_path = _bookmark_parent_folder(folder_path)
        parent_node = nodes[parent_path]
        folder_node = BookmarkFolderNode(path=folder_path)
        nodes[folder_path] = folder_node
        parent_node.folders.append(folder_node)

    for bookmark in collection.bookmarks:
        target_node = nodes.get(bookmark.folder, root)
        target_node.bookmarks.append(bookmark)

    return root


def _parse_folders(raw_entries: object) -> list[BookmarkFolder]:
    folders: list[BookmarkFolder] = []
    seen_paths: set[str] = set()
    if not _is_object_list(raw_entries):
        return folders
    for raw_entry in raw_entries:
        if not _is_string_object_dict(raw_entry):
            continue
        folder_path = normalize_bookmark_folder_path(
            _entry_string_value(raw_entry, "path")
        )
        if not folder_path or folder_path in seen_paths:
            continue
        folders.append(BookmarkFolder(path=folder_path))
        seen_paths.add(folder_path)
    return folders


def _parse_bookmarks(raw_entries: object) -> list[Bookmark]:
    bookmarks: list[Bookmark] = []
    seen_paths: set[str] = set()
    if not _is_object_list(raw_entries):
        return bookmarks
    for raw_entry in raw_entries:
        if not _is_string_object_dict(raw_entry):
            continue
        label = _entry_string_value(raw_entry, "label").strip()
        path_text = _entry_string_value(raw_entry, "path").strip()
        if not label or not path_text:
            continue
        bookmark_path = Path(normalize_windows_path_text(path_text)).expanduser()
        dedupe_key = path_key(bookmark_path)
        if dedupe_key in seen_paths:
            continue
        bookmarks.append(
            Bookmark(
                label=label,
                path=bookmark_path,
                folder=normalize_bookmark_folder_path(
                    _entry_string_value(raw_entry, "folder")
                ),
            )
        )
        seen_paths.add(dedupe_key)
    return bookmarks


def _is_object_list(value: object) -> TypeGuard[list[object]]:
    """Return whether the value is a plain object list."""

    return isinstance(value, list)


def _is_string_object_dict(value: object) -> TypeGuard[dict[str, object]]:
    """Return whether the value is a string-keyed object mapping."""

    if not isinstance(value, dict):
        return False
    raw_mapping = cast("dict[object, object]", value)
    return all(isinstance(key, str) for key in raw_mapping)


def _entry_string_value(entry: dict[str, object], key: str) -> str:
    """Return one mapping value coerced to string for bookmark parsing."""

    return str(entry.get(key, ""))


def _append_folder_path_with_parents(
    ordered_paths: list[str],
    seen_paths: set[str],
    folder_path: str,
) -> None:
    normalized = normalize_bookmark_folder_path(folder_path)
    if not normalized:
        return
    parent = _bookmark_parent_folder(normalized)
    if parent:
        _append_folder_path_with_parents(ordered_paths, seen_paths, parent)
    if normalized in seen_paths:
        return
    ordered_paths.append(normalized)
    seen_paths.add(normalized)


def _bookmark_parent_folder(folder_path: str) -> str:
    normalized = normalize_bookmark_folder_path(folder_path)
    if "/" not in normalized:
        return ""
    return normalized.rsplit("/", 1)[0]


def _serialize_collection(collection: BookmarkCollection) -> str:
    """Serialize folders and bookmarks into the canonical TOML form."""

    chunks: list[str] = []
    for folder in collection.folders:
        chunks.append("[[folders]]\n")
        chunks.append(f"path = {json.dumps(folder.path)}\n")
        chunks.append("\n")
    for bookmark in collection.bookmarks:
        chunks.append("[[bookmarks]]\n")
        chunks.append(f"label = {json.dumps(bookmark.label)}\n")
        chunks.append(f"path = {json.dumps(str(bookmark.path))}\n")
        if bookmark.folder:
            chunks.append(f"folder = {json.dumps(bookmark.folder)}\n")
        chunks.append("\n")
    return "".join(chunks).rstrip() + ("\n" if chunks else "")
