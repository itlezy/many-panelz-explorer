"""Folder-size calculation backends with optional Everything SDK support."""

from __future__ import annotations

import ctypes
import os
import threading
from pathlib import Path

from threep_commons.fs_paths import path_key

EVERYTHING_REQUEST_FILE_NAME = 0x00000001
EVERYTHING_REQUEST_PATH = 0x00000002
EVERYTHING_REQUEST_SIZE = 0x00000010
EVERYTHING_MAX_RESULTS = 32
EVERYTHING_DLL_NAME = "Everything64.dll"


class FolderSizeCalculator:
    """Calculate folder sizes with one concrete backend."""

    label = "Native recursive"
    uses_everything_sdk = False

    def calculate(self, path: Path) -> int:
        """Return the total size in bytes for one folder.

        Args:
            path: Folder whose recursive size should be calculated.

        Returns:
            Total byte size for the folder.
        """

        return native_recursive_folder_size(path)


class _EverythingSdkFolderSizeCalculator(FolderSizeCalculator):
    """Query folder sizes through the Everything SDK when indexed."""

    label = "Everything SDK"
    uses_everything_sdk = True

    def __init__(self, dll_path: Path) -> None:
        """Load and configure the Everything SDK DLL.

        Args:
            dll_path: Full path to `Everything64.dll`.
        """

        self._dll_path = Path(dll_path)
        self._lock = threading.Lock()
        self._dll = ctypes.WinDLL(str(self._dll_path))
        self._configure_dll()

    def calculate(self, path: Path) -> int:
        """Return the indexed folder size for one folder.

        Args:
            path: Folder whose size should be queried.

        Returns:
            Indexed folder size in bytes.

        Raises:
            RuntimeError: If the SDK cannot return the folder size.
        """

        target = Path(path)
        if not target.exists() or not target.is_dir():
            raise RuntimeError(f"Folder is unavailable: {target}")
        with self._lock:
            self._dll.Everything_Reset()
            self._dll.Everything_SetRequestFlags(
                EVERYTHING_REQUEST_FILE_NAME
                | EVERYTHING_REQUEST_PATH
                | EVERYTHING_REQUEST_SIZE
            )
            self._dll.Everything_SetMatchPath(True)
            self._dll.Everything_SetMatchWholeWord(True)
            self._dll.Everything_SetRegex(False)
            self._dll.Everything_SetMax(EVERYTHING_MAX_RESULTS)
            self._dll.Everything_SetSearchW(str(target))
            if not bool(self._dll.Everything_QueryW(True)):
                raise RuntimeError(self._error_text("Everything query failed."))
            result_count = int(self._dll.Everything_GetNumResults())
            target_key = path_key(target)
            for index in range(result_count):
                if not bool(self._dll.Everything_IsFolderResult(index)):
                    continue
                candidate = self._result_full_path(index)
                if not candidate or path_key(Path(candidate)) != target_key:
                    continue
                size_value = ctypes.c_longlong()
                if not bool(
                    self._dll.Everything_GetResultSize(index, ctypes.byref(size_value))
                ):
                    raise RuntimeError(
                        self._error_text("Everything did not return a folder size.")
                    )
                return _normalize_size_value(int(size_value.value))
            raise RuntimeError("Folder is not indexed by Everything.")

    def _configure_dll(self) -> None:
        """Configure the ctypes signatures for the used Everything APIs."""

        self._dll.Everything_Reset.argtypes = []
        self._dll.Everything_Reset.restype = None
        self._dll.Everything_SetSearchW.argtypes = [ctypes.c_wchar_p]
        self._dll.Everything_SetSearchW.restype = None
        self._dll.Everything_SetRequestFlags.argtypes = [ctypes.c_uint]
        self._dll.Everything_SetRequestFlags.restype = None
        self._dll.Everything_SetMatchPath.argtypes = [ctypes.c_bool]
        self._dll.Everything_SetMatchPath.restype = None
        self._dll.Everything_SetMatchWholeWord.argtypes = [ctypes.c_bool]
        self._dll.Everything_SetMatchWholeWord.restype = None
        self._dll.Everything_SetRegex.argtypes = [ctypes.c_bool]
        self._dll.Everything_SetRegex.restype = None
        self._dll.Everything_SetMax.argtypes = [ctypes.c_uint]
        self._dll.Everything_SetMax.restype = None
        self._dll.Everything_QueryW.argtypes = [ctypes.c_bool]
        self._dll.Everything_QueryW.restype = ctypes.c_bool
        self._dll.Everything_GetNumResults.argtypes = []
        self._dll.Everything_GetNumResults.restype = ctypes.c_uint
        self._dll.Everything_IsFolderResult.argtypes = [ctypes.c_uint]
        self._dll.Everything_IsFolderResult.restype = ctypes.c_bool
        self._dll.Everything_GetResultFullPathNameW.argtypes = [
            ctypes.c_uint,
            ctypes.c_wchar_p,
            ctypes.c_uint,
        ]
        self._dll.Everything_GetResultFullPathNameW.restype = ctypes.c_uint
        self._dll.Everything_GetResultSize.argtypes = [
            ctypes.c_uint,
            ctypes.POINTER(ctypes.c_longlong),
        ]
        self._dll.Everything_GetResultSize.restype = ctypes.c_bool
        self._dll.Everything_GetLastError.argtypes = []
        self._dll.Everything_GetLastError.restype = ctypes.c_uint

    def _result_full_path(self, index: int) -> str:
        """Return one result full path from the Everything SDK."""

        buffer = ctypes.create_unicode_buffer(32768)
        copied = int(
            self._dll.Everything_GetResultFullPathNameW(
                int(index),
                buffer,
                len(buffer),
            )
        )
        if copied <= 0:
            return ""
        return str(buffer.value)

    def _error_text(self, message: str) -> str:
        """Append the Everything error code to one message."""

        error_code = int(self._dll.Everything_GetLastError())
        return f"{message} (Everything error {error_code})"


class _HybridEverythingFolderSizeCalculator(FolderSizeCalculator):
    """Prefer the Everything SDK and fall back to native recursion per folder."""

    label = "Everything SDK"
    uses_everything_sdk = True

    def __init__(self, dll_path: Path) -> None:
        """Build one hybrid calculator around the detected SDK DLL.

        Args:
            dll_path: Full path to `Everything64.dll`.
        """

        self._sdk = _EverythingSdkFolderSizeCalculator(dll_path)

    def calculate(self, path: Path) -> int:
        """Return the best available folder size for one folder.

        Args:
            path: Folder whose size should be calculated.

        Returns:
            Total byte size for the folder.
        """

        try:
            return self._sdk.calculate(path)
        except RuntimeError:
            return native_recursive_folder_size(path)


def build_folder_size_calculator(
    *,
    use_everything_sdk: bool,
    everything_executable: str,
) -> FolderSizeCalculator:
    """Return the preferred folder-size calculator for the current settings.

    Args:
        use_everything_sdk: Whether the SDK path should be attempted.
        everything_executable: Configured Everything executable path.

    Returns:
        One calculator instance for the requested backend policy.
    """

    if not use_everything_sdk:
        return FolderSizeCalculator()
    dll_path = find_everything_sdk_dll(everything_executable=everything_executable)
    if dll_path is None:
        return FolderSizeCalculator()
    return _HybridEverythingFolderSizeCalculator(dll_path)


def find_everything_sdk_dll(*, everything_executable: str) -> Path | None:
    """Detect `Everything64.dll` from local installation paths only.

    Args:
        everything_executable: Configured Everything executable path.

    Returns:
        Full DLL path when found, otherwise `None`.
    """

    configured_executable = Path(str(everything_executable or "").strip())
    candidate_paths: list[Path] = []
    if configured_executable.name:
        candidate_paths.append(configured_executable.with_name(EVERYTHING_DLL_NAME))
    candidate_paths.extend(
        [
            Path(r"C:\Program Files\Everything\Everything64.dll"),
            Path(r"C:\Program Files (x86)\Everything\Everything64.dll"),
            Path(os.path.expandvars(r"%PROGRAMFILES%\Everything\Everything64.dll")),
            Path(os.path.expandvars(r"%PROGRAMFILES(X86)%\Everything\Everything64.dll")),
            Path.cwd() / EVERYTHING_DLL_NAME,
        ]
    )
    for candidate in candidate_paths:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def native_recursive_folder_size(path: Path) -> int:
    """Return the recursive byte size for one folder without following symlinks.

    Args:
        path: Folder whose size should be calculated.

    Returns:
        Recursive byte size for the folder.

    Raises:
        OSError: If the top-level folder cannot be scanned.
    """

    total_size = 0
    pending: list[Path] = [Path(path)]
    while pending:
        current = pending.pop()
        with os.scandir(current) as iterator:
            for entry in iterator:
                try:
                    if entry.is_symlink():
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(Path(entry.path))
                        continue
                    entry_stat = entry.stat(follow_symlinks=False)
                except OSError:
                    continue
                total_size += int(entry_stat.st_size)
    return total_size


def _normalize_size_value(value: int) -> int:
    """Normalize signed 64-bit Everything size values to Python ints."""

    if value >= 0:
        return int(value)
    return int((1 << 64) + value)
