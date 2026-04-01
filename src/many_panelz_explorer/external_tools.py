"""External shortcut tool launch helpers."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from threep_commons.executables import resolve_executable_path
from threep_commons.fs_paths import is_explicit_path_text, normalize_windows_path_text
from threep_commons.subprocess_helpers import (
    merge_subprocess_kwargs,
    windows_no_window_popen_kwargs,
)

DEFAULT_EVERYTHING_EXECUTABLE = "Everything.exe"
EVERYTHING_DISCOVERY_CANDIDATES = (DEFAULT_EVERYTHING_EXECUTABLE,)

DEFAULT_SEVEN_ZIP_EXECUTABLE = "7z.exe"
SEVEN_ZIP_DISCOVERY_CANDIDATES = (DEFAULT_SEVEN_ZIP_EXECUTABLE, "7za.exe")
DEFAULT_SEVEN_ZIP_PACK_ARGS_TEMPLATE = (
    "a -y {archive} {sources} {recurse_mode} {compression_level} "
    "{method_mode} {solid_mode} {header_mode}"
)
DEFAULT_SEVEN_ZIP_EXTRACT_ARGS_TEMPLATE = (
    "{extract_mode} -y {archive} -o{target} {overwrite_mode}"
)

DEFAULT_WINRAR_EXECUTABLE = "WinRAR.exe"
WINRAR_DISCOVERY_CANDIDATES = (DEFAULT_WINRAR_EXECUTABLE, "rar.exe")
DEFAULT_WINRAR_PACK_ARGS_TEMPLATE = (
    "a {recurse_mode} {compression_level} {solid_mode} {recovery_mode} "
    "{lock_mode} {archive} {sources}"
)
DEFAULT_WINRAR_EXTRACT_ARGS_TEMPLATE = (
    "{extract_mode} -y {archive} {target} {overwrite_mode} {keep_broken_mode}"
)


def resolve_tool_executable(executable: str, *, tool_name: str) -> Path:
    """Resolve one configured external-tool executable.

    Args:
        executable: Configured executable text or explicit path.
        tool_name: Human-readable tool name for error messages.

    Returns:
        The resolved executable path.

    Raises:
        RuntimeError: If the tool is not configured or cannot be resolved.
    """

    normalized = normalize_windows_path_text(str(executable or "").strip())
    if not normalized:
        raise RuntimeError(f"{tool_name} is not configured.")
    resolved = resolve_executable_path(normalized)
    if resolved is not None:
        return Path(resolved)
    if is_explicit_path_text(normalized):
        raise RuntimeError(f"{tool_name} executable does not exist: {normalized}")
    raise RuntimeError(f"{tool_name} is unavailable: {normalized}")


def expand_tool_args(
    template: str,
    *,
    archive: Path | None = None,
    target: Path | None = None,
) -> list[str]:
    """Expand one external-tool template into argv tokens.

    Args:
        template: Raw argument template string.
        archive: Archive placeholder replacement.
        target: Destination placeholder replacement.

    Returns:
        Expanded argv tokens with empty tokens removed.
    """

    tokens = shlex.split(str(template or "").strip(), posix=False)
    replacements = {
        "{archive}": str(archive) if archive is not None else "",
        "{target}": str(target) if target is not None else "",
    }
    expanded: list[str] = []
    for token in tokens:
        rendered = token
        for placeholder, value in replacements.items():
            rendered = rendered.replace(placeholder, value)
        if rendered:
            expanded.append(rendered)
    return expanded


def launch_everything_search(*, executable: str, path: Path) -> None:
    """Launch Everything scoped to the provided path.

    Args:
        executable: Configured Everything executable.
        path: Active filesystem path to search under.

    Raises:
        RuntimeError: If the tool cannot be launched.
    """

    resolved = resolve_tool_executable(executable, tool_name="Everything")
    _launch_process(
        [str(resolved), "-path", str(Path(path))],
        tool_name="Everything",
    )


def launch_archive_extract(
    *,
    executable: str,
    args_template: str,
    archive: Path,
    target: Path,
    tool_name: str,
) -> None:
    """Launch one external archive extractor for the provided archive.

    Args:
        executable: Configured extractor executable.
        args_template: Extraction argument template using `{archive}` and `{target}`.
        archive: Archive file to extract.
        target: Destination directory.
        tool_name: Human-readable tool name for error messages.

    Raises:
        RuntimeError: If the tool cannot be resolved or launched.
    """

    resolved = resolve_tool_executable(executable, tool_name=tool_name)
    args = expand_tool_args(
        args_template,
        archive=Path(archive),
        target=Path(target),
    )
    if not args:
        raise RuntimeError(f"{tool_name} extract args are empty.")
    _launch_process([str(resolved), *args], tool_name=tool_name)


def _launch_process(args: list[str], *, tool_name: str) -> None:
    """Launch one detached external process.

    Args:
        args: Full argv to launch.
        tool_name: Human-readable tool name for error messages.

    Raises:
        RuntimeError: If the process could not be started.
    """

    try:
        subprocess.Popen(
            args,
            **merge_subprocess_kwargs(windows_no_window_popen_kwargs()),
        )
    except OSError as exc:
        raise RuntimeError(f"{tool_name} launch failed: {exc}") from exc
