import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")
pytest.importorskip("pytestqt")

from many_panelz_explorer._settings.models import UiPreferences
from many_panelz_explorer.dialogs.archive_operation_dialog import (
    ArchiveOperationDialog,
)


def _set_combo_data(combo, value: str) -> None:
    """Select one combo-box row by its item data."""

    for index in range(combo.count()):
        if str(combo.itemData(index)) == value:
            combo.setCurrentIndex(index)
            return
    msg = f"Missing combo data: {value}"
    raise AssertionError(msg)


def test_pack_dialog_switches_backend_options_and_preserves_target_stem(
    qtbot,
    tmp_path: Path,
) -> None:
    source = tmp_path / "alpha.txt"
    source.write_text("alpha", encoding="utf-8")
    preferences = UiPreferences(default_archive_packer_backend="archive_7zip")

    dialog = ArchiveOperationDialog(
        kind="pack",
        sources=[source],
        preferences=preferences,
    )
    qtbot.addWidget(dialog)
    dialog.show()

    assert str(dialog.backend_combo.currentData()) == "archive_7zip"
    assert Path(dialog.target_edit.text()).suffix == ".7z"
    assert dialog.seven_zip_pack_group.isVisible() is True
    assert dialog.winrar_pack_group.isVisible() is False

    custom_target = tmp_path / "archives" / "bundle.7z"
    dialog.target_edit.setText(str(custom_target))

    _set_combo_data(dialog.backend_combo, "archive_winrar")
    qtbot.waitUntil(lambda: Path(dialog.target_edit.text()).suffix == ".rar")

    assert Path(dialog.target_edit.text()) == custom_target.with_suffix(".rar")
    assert dialog.winrar_pack_group.isVisible() is True
    assert dialog.seven_zip_pack_group.isVisible() is False


def test_pack_dialog_build_request_uses_selected_backend_options(
    qtbot,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.bin"
    source.write_text("payload", encoding="utf-8")
    preferences = UiPreferences(default_archive_packer_backend="archive_7zip")

    dialog = ArchiveOperationDialog(
        kind="pack",
        sources=[source],
        preferences=preferences,
    )
    qtbot.addWidget(dialog)
    dialog.show()

    _set_combo_data(dialog.backend_combo, "archive_7zip")
    dialog.seven_zip_pack_recurse_checkbox.setChecked(False)
    _set_combo_data(dialog.seven_zip_pack_level_combo, "-mx=9")
    _set_combo_data(dialog.seven_zip_pack_method_combo, "-m0=LZMA")
    dialog.seven_zip_pack_solid_checkbox.setChecked(False)
    dialog.seven_zip_pack_header_checkbox.setChecked(False)
    dialog.pack_password_edit.setText("secret")
    dialog.pack_encrypt_names_checkbox.setChecked(True)
    dialog.pack_split_size_edit.setText("100m")
    dialog.pack_sfx_checkbox.setChecked(True)
    dialog.pack_test_checkbox.setChecked(True)
    dialog.seven_zip_pack_extra_args_edit.setText("-mmt=on")
    dialog.target_edit.setText(str(tmp_path / "bundle"))

    request = dialog.build_request(created_by="test:archive-pack")

    assert request.kind == "pack"
    assert request.backend_id == "archive_7zip"
    assert request.target_dir is None
    assert request.target_path == (tmp_path / "bundle.7z")
    assert request.dispatch_mode == preferences.default_operation_dispatch_mode
    assert request.conflict_policy == preferences.default_operation_conflict_policy
    assert request.backend_options == {
        "recurse_mode": "",
        "compression_level": "-mx=9",
        "method_mode": "-m0=LZMA",
        "solid_mode": "",
        "header_mode": "",
        "password_mode": "-psecret",
        "header_encrypt_mode": "-mhe=on",
        "volume_mode": "-v100m",
        "sfx_mode": "-sfx",
        "test_mode": "-t",
        "extra_args": "-mmt=on",
    }


def test_unpack_dialog_build_request_uses_selected_backend_options(
    qtbot,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "sample.7z"
    archive.write_text("archive", encoding="utf-8")
    preferences = UiPreferences(default_archive_unpacker_backend="archive_7zip")

    dialog = ArchiveOperationDialog(
        kind="unpack",
        sources=[archive],
        preferences=preferences,
    )
    qtbot.addWidget(dialog)
    dialog.show()

    assert str(dialog.backend_combo.currentData()) == "archive_7zip"
    assert dialog.seven_zip_unpack_group.isVisible() is True
    assert dialog.winrar_unpack_group.isVisible() is False

    _set_combo_data(dialog.seven_zip_unpack_mode_combo, "e")
    _set_combo_data(dialog.seven_zip_unpack_overwrite_combo, "-aou")
    dialog.seven_zip_unpack_extra_args_edit.setText("-bb1")
    dialog.target_edit.setText(str(tmp_path / "unpacked"))

    request = dialog.build_request(created_by="test:archive-unpack")

    assert request.kind == "unpack"
    assert request.backend_id == "archive_7zip"
    assert request.target_path is None
    assert request.target_dir == (tmp_path / "unpacked")
    assert request.backend_options == {
        "extract_mode": "e",
        "overwrite_mode": "-aou",
        "password_mode": "",
        "extra_args": "-bb1",
    }


def test_unpack_dialog_build_request_uses_winrar_options(
    qtbot,
    tmp_path: Path,
) -> None:
    archive = tmp_path / "sample.rar"
    archive.write_text("archive", encoding="utf-8")
    preferences = UiPreferences(default_archive_unpacker_backend="archive_winrar")

    dialog = ArchiveOperationDialog(
        kind="unpack",
        sources=[archive],
        preferences=preferences,
    )
    qtbot.addWidget(dialog)
    dialog.show()

    assert str(dialog.backend_combo.currentData()) == "archive_winrar"
    assert dialog.winrar_unpack_group.isVisible() is True
    assert dialog.seven_zip_unpack_group.isVisible() is False

    _set_combo_data(dialog.winrar_unpack_mode_combo, "e")
    _set_combo_data(dialog.winrar_unpack_overwrite_combo, "-o+")
    dialog.winrar_unpack_keep_broken_checkbox.setChecked(True)
    dialog.unpack_password_edit.setText("rarpass")
    dialog.winrar_unpack_extra_args_edit.setText("-ibck")
    dialog.target_edit.setText(str(tmp_path / "unpacked-rar"))

    request = dialog.build_request(created_by="test:archive-unpack-winrar")

    assert request.kind == "unpack"
    assert request.backend_id == "archive_winrar"
    assert request.target_path is None
    assert request.target_dir == (tmp_path / "unpacked-rar")
    assert request.backend_options == {
        "extract_mode": "e",
        "overwrite_mode": "-o+",
        "keep_broken_mode": "-kb",
        "password_mode": "-prarpass",
        "extra_args": "-ibck",
    }


def test_pack_dialog_build_request_uses_winrar_common_options(
    qtbot,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.txt"
    source.write_text("payload", encoding="utf-8")
    preferences = UiPreferences(default_archive_packer_backend="archive_winrar")

    dialog = ArchiveOperationDialog(
        kind="pack",
        sources=[source],
        preferences=preferences,
    )
    qtbot.addWidget(dialog)
    dialog.show()

    assert str(dialog.backend_combo.currentData()) == "archive_winrar"
    dialog.pack_password_edit.setText("topsecret")
    dialog.pack_encrypt_names_checkbox.setChecked(True)
    dialog.pack_split_size_edit.setText("700m")
    dialog.pack_sfx_checkbox.setChecked(True)
    dialog.pack_test_checkbox.setChecked(True)
    _set_combo_data(dialog.winrar_pack_level_combo, "-m5")
    dialog.winrar_pack_lock_checkbox.setChecked(True)

    request = dialog.build_request(created_by="test:archive-pack-winrar")

    assert request.backend_id == "archive_winrar"
    assert request.backend_options["compression_level"] == "-m5"
    assert request.backend_options["lock_mode"] == "-k"
    assert request.backend_options["password_mode"] == "-hptopsecret"
    assert request.backend_options["volume_mode"] == "-v700m"
    assert request.backend_options["sfx_mode"] == "-sfx"
    assert request.backend_options["test_mode"] == "-t"
