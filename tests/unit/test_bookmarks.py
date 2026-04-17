from __future__ import annotations

from pathlib import Path

from many_panelz_explorer.bookmarks import (
    Bookmark,
    BookmarkCollection,
    BookmarkFolder,
    BookmarkStore,
    build_bookmark_tree,
    collect_folder_paths,
    default_bookmark_label,
)


class _SettingsPathStub:
    def __init__(self, settings_path: Path) -> None:
        self.settings_path = settings_path


def test_bookmark_store_uses_sibling_toml_path_for_settings_file(
    tmp_path: Path,
) -> None:
    settings = _SettingsPathStub(tmp_path / "many_panelz_explorer.ini")

    store = BookmarkStore.from_settings(settings)

    assert store.bookmarks_file == tmp_path / "many_panelz_explorer.bookmarks.toml"


def test_bookmark_store_missing_file_yields_empty_collection(tmp_path: Path) -> None:
    store = BookmarkStore(tmp_path / "bookmarks.toml")

    assert store.load() == BookmarkCollection()


def test_bookmark_store_round_trip_preserves_folder_and_bookmark_order(
    tmp_path: Path,
) -> None:
    store = BookmarkStore(tmp_path / "bookmarks.toml")
    collection = BookmarkCollection(
        folders=(
            BookmarkFolder(path="Work"),
            BookmarkFolder(path="Work/Clients"),
        ),
        bookmarks=(
            Bookmark(label="Repo", path=tmp_path / "repo", folder="Work"),
            Bookmark(
                label="Client Docs",
                path=tmp_path / "docs",
                folder="Work/Clients",
            ),
        ),
    )

    store.save(collection)

    assert store.load() == collection


def test_bookmark_store_loads_legacy_flat_bookmarks_at_root(tmp_path: Path) -> None:
    bookmarks_file = tmp_path / "bookmarks.toml"
    bookmarks_file.write_text(
        "\n".join(
            [
                "[[bookmarks]]",
                'label = "Repo"',
                'path = "C:\\\\prj\\\\repo"',
                "",
                "[[bookmarks]]",
                'label = "Docs"',
                'path = "C:\\\\docs"',
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    store = BookmarkStore(bookmarks_file)

    assert store.load() == BookmarkCollection(
        bookmarks=(
            Bookmark(label="Repo", path=Path("C:/prj/repo")),
            Bookmark(label="Docs", path=Path("C:/docs")),
        )
    )


def test_bookmark_store_skips_incomplete_invalid_and_duplicate_entries(
    tmp_path: Path,
) -> None:
    bookmarks_file = tmp_path / "bookmarks.toml"
    bookmarks_file.write_text(
        "\n".join(
            [
                "[[folders]]",
                'path = "Work"',
                "",
                "[[folders]]",
                'path = "Work"',
                "",
                "[[folders]]",
                'path = ""',
                "",
                "[[bookmarks]]",
                'label = "Repo"',
                'path = "C:\\\\prj\\\\repo"',
                'folder = "Work"',
                "",
                "[[bookmarks]]",
                'label = ""',
                'path = "C:\\\\ignored\\\\empty-label"',
                "",
                "[[bookmarks]]",
                'label = "Repo duplicate"',
                'path = "C:\\\\prj\\\\repo"',
                'folder = "Work/Clients"',
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    store = BookmarkStore(bookmarks_file)

    assert store.load() == BookmarkCollection(
        folders=(BookmarkFolder(path="Work"),),
        bookmarks=(Bookmark(label="Repo", path=Path("C:/prj/repo"), folder="Work"),),
    )


def test_collect_folder_paths_and_tree_auto_materialize_missing_parents(
    tmp_path: Path,
) -> None:
    collection = BookmarkCollection(
        folders=(BookmarkFolder(path="Work/Clients"),),
        bookmarks=(
            Bookmark(
                label="Repo",
                path=tmp_path / "repo",
                folder="Work/Clients/ClientA",
            ),
        ),
    )

    assert collect_folder_paths(collection) == (
        "Work",
        "Work/Clients",
        "Work/Clients/ClientA",
    )

    tree = build_bookmark_tree(collection)

    assert [folder.path for folder in tree.folders] == ["Work"]
    assert [folder.path for folder in tree.folders[0].folders] == ["Work/Clients"]
    assert [folder.path for folder in tree.folders[0].folders[0].folders] == [
        "Work/Clients/ClientA"
    ]
    assert tree.folders[0].folders[0].folders[0].bookmarks == [
        Bookmark(
            label="Repo",
            path=tmp_path / "repo",
            folder="Work/Clients/ClientA",
        )
    ]


def test_bookmark_store_add_update_remove_and_create_folder(tmp_path: Path) -> None:
    store = BookmarkStore(tmp_path / "bookmarks.toml")
    first_path = tmp_path / "alpha"
    second_path = tmp_path / "beta"

    created_folder = store.create_folder("Work/Clients")
    first_save = store.add_or_update(
        path=first_path,
        label="Alpha",
        folder="Work",
    )
    second_save = store.add_or_update(
        path=second_path,
        label="Beta",
        folder="Work/Clients",
    )
    updated = store.add_or_update(
        path=first_path,
        label="Alpha Renamed",
        folder="Work/Clients",
    )
    removed = store.remove(path=second_path)

    assert created_folder == BookmarkCollection(
        folders=(BookmarkFolder(path="Work/Clients"),),
    )
    assert first_save == BookmarkCollection(
        folders=(BookmarkFolder(path="Work/Clients"),),
        bookmarks=(Bookmark(label="Alpha", path=first_path, folder="Work"),),
    )
    assert second_save == BookmarkCollection(
        folders=(BookmarkFolder(path="Work/Clients"),),
        bookmarks=(
            Bookmark(label="Alpha", path=first_path, folder="Work"),
            Bookmark(label="Beta", path=second_path, folder="Work/Clients"),
        ),
    )
    assert updated == BookmarkCollection(
        folders=(BookmarkFolder(path="Work/Clients"),),
        bookmarks=(
            Bookmark(
                label="Alpha Renamed",
                path=first_path,
                folder="Work/Clients",
            ),
            Bookmark(label="Beta", path=second_path, folder="Work/Clients"),
        ),
    )
    assert removed == BookmarkCollection(
        folders=(BookmarkFolder(path="Work/Clients"),),
        bookmarks=(
            Bookmark(
                label="Alpha Renamed",
                path=first_path,
                folder="Work/Clients",
            ),
        ),
    )


def test_default_bookmark_label_uses_folder_name_when_available(tmp_path: Path) -> None:
    assert default_bookmark_label(tmp_path / "workspace") == "workspace"
    assert default_bookmark_label(Path("C:/")) == "C:\\"
