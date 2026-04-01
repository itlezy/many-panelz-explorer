from __future__ import annotations

from pathlib import Path

from many_panelz_explorer import folder_sizes


class _FakeHybridCalculator(folder_sizes.FolderSizeCalculator):
    label = "Everything SDK"
    uses_everything_sdk = True

    def __init__(self, dll_path: Path) -> None:
        self.dll_path = Path(dll_path)


def test_find_everything_sdk_dll_prefers_configured_executable_directory(
    tmp_path: Path,
) -> None:
    everything_executable = tmp_path / "Everything.exe"
    dll_path = tmp_path / "Everything64.dll"
    everything_executable.write_text("", encoding="utf-8")
    dll_path.write_text("", encoding="utf-8")

    detected = folder_sizes.find_everything_sdk_dll(
        everything_executable=str(everything_executable)
    )

    assert detected == dll_path


def test_native_recursive_folder_size_sums_nested_files(tmp_path: Path) -> None:
    root = tmp_path / "root"
    nested = root / "nested"
    nested.mkdir(parents=True)
    (root / "a.bin").write_bytes(b"abcd")
    (nested / "b.bin").write_bytes(b"123456")

    assert folder_sizes.native_recursive_folder_size(root) == 10


def test_build_folder_size_calculator_uses_native_when_sdk_disabled() -> None:
    calculator = folder_sizes.build_folder_size_calculator(
        use_everything_sdk=False,
        everything_executable="",
    )

    assert calculator.uses_everything_sdk is False
    assert calculator.label == "Native recursive"


def test_build_folder_size_calculator_prefers_everything_sdk_when_available(
    monkeypatch,
    tmp_path: Path,
) -> None:
    dll_path = tmp_path / "Everything64.dll"
    dll_path.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        folder_sizes,
        "find_everything_sdk_dll",
        lambda *, everything_executable: dll_path,
    )
    monkeypatch.setattr(
        folder_sizes,
        "_HybridEverythingFolderSizeCalculator",
        _FakeHybridCalculator,
    )

    calculator = folder_sizes.build_folder_size_calculator(
        use_everything_sdk=True,
        everything_executable=r"C:\tools\Everything.exe",
    )

    assert calculator.uses_everything_sdk is True
    assert calculator.label == "Everything SDK"
    assert isinstance(calculator, _FakeHybridCalculator)
    assert calculator.dll_path == dll_path
