"""Typed operation request, result, and queue models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from pathlib import Path


OperationKind = Literal["copy", "move", "delete", "pack", "unpack"]
OperationStatus = Literal[
    "queued",
    "running",
    "dispatched",
    "succeeded",
    "failed",
    "cancelled",
]
OperationDispatchMode = Literal["queue", "launch_now_no_wait", "run_now_wait"]
OperationConflictPolicy = Literal["overwrite", "skip", "rename", "cancel"]
TerminalLauncherId = Literal[
    "comspec",
    "pwsh",
    "powershell5",
    "windows_terminal",
    "alacritty",
    "wezterm",
]
TerminalStartupPosition = Literal[
    "normal",
    "maximized",
    "minimized",
    "right_of_screen",
    "left_of_screen",
]
CopyMoveBackendId = Literal[
    "python_builtin",
    "windows_explorer",
    "robocopy",
    "teracopy",
    "unstoppable",
    "external_copymove",
]
DeleteBackendId = Literal[
    "recycle_bin",
    "permanent_native",
    "cmd_delete",
    "powershell_delete",
    "rimraf",
    "external_delete",
]
ArchiveBackendId = Literal["archive_winrar", "archive_7zip"]
OperationBackendId = CopyMoveBackendId | DeleteBackendId | ArchiveBackendId

DISPATCH_MODE_QUEUE: OperationDispatchMode = "queue"
DISPATCH_MODE_LAUNCH_NO_WAIT: OperationDispatchMode = "launch_now_no_wait"
DISPATCH_MODE_RUN_WAIT: OperationDispatchMode = "run_now_wait"

SHORTCUT_BEHAVIOR_DIRECT: str = "direct_enqueue"
SHORTCUT_BEHAVIOR_DIALOG: str = "always_dialog"

QUEUE_VIEW_DOCK: str = "dock_tab"
QUEUE_VIEW_FLOATING: str = "floating_window"
QUEUE_VIEW_BOTH: str = "both"

BACKEND_PYTHON: CopyMoveBackendId = "python_builtin"
BACKEND_EXPLORER: CopyMoveBackendId = "windows_explorer"
BACKEND_ROBOCOPY: CopyMoveBackendId = "robocopy"
BACKEND_TERACOPY: CopyMoveBackendId = "teracopy"
BACKEND_UNSTOPPABLE: CopyMoveBackendId = "unstoppable"
BACKEND_EXTERNAL_COPYMOVE: CopyMoveBackendId = "external_copymove"

BACKEND_RECYCLE_BIN: DeleteBackendId = "recycle_bin"
BACKEND_PERMANENT_NATIVE: DeleteBackendId = "permanent_native"
BACKEND_CMD_DELETE: DeleteBackendId = "cmd_delete"
BACKEND_POWERSHELL_DELETE: DeleteBackendId = "powershell_delete"
BACKEND_RIMRAF: DeleteBackendId = "rimraf"
BACKEND_EXTERNAL_DELETE: DeleteBackendId = "external_delete"
BACKEND_ARCHIVE_WINRAR: ArchiveBackendId = "archive_winrar"
BACKEND_ARCHIVE_7ZIP: ArchiveBackendId = "archive_7zip"

DEFAULT_TERA_COPY_EXE = "TeraCopy.exe"
DEFAULT_TERA_COPY_ARGS = "{operation} {sources} {target}"
DEFAULT_UNSTOPPABLE_EXE = "UnstoppableCopier.exe"
DEFAULT_UNSTOPPABLE_ARGS = ""
DEFAULT_GENERIC_COPYMOVE_EXE = ""
DEFAULT_GENERIC_COPYMOVE_ARGS = "{operation} {sources} {target}"
DEFAULT_GENERIC_DELETE_EXE = ""
DEFAULT_GENERIC_DELETE_ARGS = "{operation} {sources}"
DEFAULT_SEVEN_ZIP_PACK_ARGS = (
    "a -y {archive} {sources} {recurse_mode} {compression_level} "
    "{method_mode} {solid_mode} {header_mode}"
)
DEFAULT_SEVEN_ZIP_UNPACK_ARGS = (
    "{extract_mode} -y {archive} -o{target} {overwrite_mode}"
)
DEFAULT_WINRAR_PACK_ARGS = (
    "a {recurse_mode} {compression_level} {solid_mode} {recovery_mode} "
    "{lock_mode} {archive} {sources}"
)
DEFAULT_WINRAR_UNPACK_ARGS = (
    "{extract_mode} -y {archive} {target} {overwrite_mode} {keep_broken_mode}"
)
DEFAULT_ROBOCOPY_COPY_ARGS = "/E /R:0 /W:0"
DEFAULT_ROBOCOPY_MOVE_ARGS = "/E /MOVE /R:0 /W:0"
DEFAULT_CMD_DELETE_ARGS = "/Q"
DEFAULT_POWERSHELL_DELETE_ARGS = "-Force"
DEFAULT_RIMRAF_EXE = "rimraf"
DEFAULT_RIMRAF_ARGS = ""
COMPANION_TOOL_NOT_FOUND = "<not-found>"
DEFAULT_SYSTEM_CMD_FALLBACK = ""
DEFAULT_SYSTEM_ROBOCOPY_FALLBACK = ""
DEFAULT_SYSTEM_PWSH_FALLBACK = ""
DEFAULT_SYSTEM_POWERSHELL5_FALLBACK = ""

TERMINAL_LAUNCHER_COMSPEC: TerminalLauncherId = "comspec"
TERMINAL_LAUNCHER_PWSH: TerminalLauncherId = "pwsh"
TERMINAL_LAUNCHER_POWERSHELL5: TerminalLauncherId = "powershell5"
TERMINAL_LAUNCHER_WINDOWS_TERMINAL: TerminalLauncherId = "windows_terminal"
TERMINAL_LAUNCHER_ALACRITTY: TerminalLauncherId = "alacritty"
TERMINAL_LAUNCHER_WEZTERM: TerminalLauncherId = "wezterm"
DEFAULT_TERMINAL_LAUNCHER: TerminalLauncherId = TERMINAL_LAUNCHER_COMSPEC
DEFAULT_TERMINAL_STARTUP_POSITION: TerminalStartupPosition = "normal"
DEFAULT_COMSPEC_TERMINAL_EXECUTABLE = "%ComSpec%"
DEFAULT_COMSPEC_TERMINAL_OPEN_ARGS_TEMPLATE = "/K cd /d {folder}"
DEFAULT_COMSPEC_TERMINAL_COMMAND_ARGS_TEMPLATE = "/K {shell_command}"
DEFAULT_PWSH_TERMINAL_EXECUTABLE = "pwsh.exe"
DEFAULT_PWSH_TERMINAL_OPEN_ARGS_TEMPLATE = (
    "-NoExit -Command Set-Location -LiteralPath {folder}"
)
DEFAULT_PWSH_TERMINAL_COMMAND_ARGS_TEMPLATE = "-NoExit -Command {shell_command}"
DEFAULT_POWERSHELL5_TERMINAL_EXECUTABLE = "powershell.exe"
DEFAULT_POWERSHELL5_TERMINAL_OPEN_ARGS_TEMPLATE = (
    "-NoExit -Command Set-Location -LiteralPath {folder}"
)
DEFAULT_POWERSHELL5_TERMINAL_COMMAND_ARGS_TEMPLATE = "-NoExit -Command {shell_command}"
DEFAULT_WINDOWS_TERMINAL_EXECUTABLE = "wt.exe"
DEFAULT_WINDOWS_TERMINAL_OPEN_ARGS_TEMPLATE = "-d {folder}"
DEFAULT_WINDOWS_TERMINAL_COMMAND_ARGS_TEMPLATE = (
    "new-tab -d {folder} cmd.exe /K {shell_command}"
)
DEFAULT_ALACRITTY_TERMINAL_EXECUTABLE = "alacritty.exe"
DEFAULT_ALACRITTY_TERMINAL_OPEN_ARGS_TEMPLATE = "--working-directory {folder}"
DEFAULT_ALACRITTY_TERMINAL_COMMAND_ARGS_TEMPLATE = (
    "--working-directory {folder} --hold -e cmd.exe /K {shell_command}"
)
DEFAULT_WEZTERM_TERMINAL_EXECUTABLE = "wezterm-gui.exe"
DEFAULT_WEZTERM_TERMINAL_OPEN_ARGS_TEMPLATE = "start --cwd {folder}"
DEFAULT_WEZTERM_TERMINAL_COMMAND_ARGS_TEMPLATE = (
    "start --cwd {folder} cmd.exe /K {shell_command}"
)


@dataclass(frozen=True)
class OperationExecutionPreferences:
    """Default execution preferences for queued and direct operations."""

    default_copy_move_backend: str = BACKEND_PYTHON
    default_delete_backend: str = BACKEND_RECYCLE_BIN
    default_archive_packer_backend: str = BACKEND_ARCHIVE_WINRAR
    default_archive_unpacker_backend: str = BACKEND_ARCHIVE_WINRAR
    default_dispatch_mode: str = DISPATCH_MODE_QUEUE
    default_conflict_policy: str = "rename"
    shortcut_behavior: str = SHORTCUT_BEHAVIOR_DIRECT
    queue_view_mode: str = QUEUE_VIEW_DOCK
    default_editor_executable: str = ""
    default_viewer_executable: str = ""
    file_open_overrides_json: str = "{}"
    use_extended_paths_robocopy: bool = False
    use_extended_paths_teracopy: bool = False
    use_extended_paths_unstoppable: bool = False
    use_extended_paths_external_copymove: bool = False
    use_extended_paths_cmd_delete: bool = False
    use_extended_paths_powershell_delete: bool = False
    use_extended_paths_rimraf: bool = False
    use_extended_paths_external_delete: bool = False
    teracopy_executable: str = DEFAULT_TERA_COPY_EXE
    teracopy_args_template: str = DEFAULT_TERA_COPY_ARGS
    unstoppable_executable: str = DEFAULT_UNSTOPPABLE_EXE
    unstoppable_args_template: str = DEFAULT_UNSTOPPABLE_ARGS
    generic_copymove_executable: str = DEFAULT_GENERIC_COPYMOVE_EXE
    generic_copymove_args_template: str = DEFAULT_GENERIC_COPYMOVE_ARGS
    generic_delete_executable: str = DEFAULT_GENERIC_DELETE_EXE
    generic_delete_args_template: str = DEFAULT_GENERIC_DELETE_ARGS
    seven_zip_executable: str = "7z.exe"
    seven_zip_pack_args_template: str = DEFAULT_SEVEN_ZIP_PACK_ARGS
    seven_zip_unpack_args_template: str = DEFAULT_SEVEN_ZIP_UNPACK_ARGS
    winrar_executable: str = "WinRAR.exe"
    winrar_pack_args_template: str = DEFAULT_WINRAR_PACK_ARGS
    winrar_unpack_args_template: str = DEFAULT_WINRAR_UNPACK_ARGS
    robocopy_copy_args: str = DEFAULT_ROBOCOPY_COPY_ARGS
    robocopy_move_args: str = DEFAULT_ROBOCOPY_MOVE_ARGS
    cmd_delete_args: str = DEFAULT_CMD_DELETE_ARGS
    powershell_delete_args: str = DEFAULT_POWERSHELL_DELETE_ARGS
    rimraf_executable: str = DEFAULT_RIMRAF_EXE
    rimraf_args_template: str = DEFAULT_RIMRAF_ARGS
    resolved_cmd_path: str = DEFAULT_SYSTEM_CMD_FALLBACK
    resolved_robocopy_path: str = DEFAULT_SYSTEM_ROBOCOPY_FALLBACK


@dataclass(frozen=True)
class OperationRequest:
    """Describe a single requested copy, move, or delete operation."""

    kind: OperationKind
    sources: tuple[Path, ...]
    target_dir: Path | None
    backend_id: str
    dispatch_mode: str
    conflict_policy: str
    target_path: Path | None = None
    backend_options: dict[str, str] = field(default_factory=dict)
    created_by: str = "unknown"


@dataclass(frozen=True)
class OperationResult:
    """Capture the executor outcome for an operation request."""

    status: OperationStatus
    message: str
    processed_count: int = 0
    pid: int | None = None


@dataclass(frozen=True)
class OperationArtifacts:
    """Paths to persisted job metadata, logs, and helper scripts."""

    job_dir: Path
    metadata_path: Path
    log_path: Path
    script_path: Path | None = None


@dataclass(frozen=True)
class OperationJob:
    """Represent a queued or executed operation and its runtime state."""

    job_id: str
    request: OperationRequest
    status: OperationStatus
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    message: str = ""
    artifacts: OperationArtifacts | None = None
    pid: int | None = None
    processed_count: int = 0
    cancel_requested: bool = False

    def summary(self) -> str:
        source_count = len(self.request.sources)
        if self.request.kind == "delete":
            return f"Delete {source_count} item(s)"
        if self.request.kind == "pack":
            target = (
                str(self.request.target_path)
                if self.request.target_path is not None
                else "(none)"
            )
            return f"Pack {source_count} item(s) to {target}"
        if self.request.kind == "unpack":
            target = (
                str(self.request.target_dir)
                if self.request.target_dir is not None
                else "(none)"
            )
            return f"Unpack {source_count} archive(s) to {target}"
        target = (
            str(self.request.target_dir)
            if self.request.target_dir is not None
            else "(none)"
        )
        verb = "Copy" if self.request.kind == "copy" else "Move"
        return f"{verb} {source_count} item(s) to {target}"


def utcnow() -> datetime:
    """Return the current timezone-aware UTC timestamp."""

    return datetime.now(UTC)
