"""Default operation and open-tool settings."""

from __future__ import annotations

from threep_commons.settings import SettingsDomainBase

from many_panelz_explorer._operations.normalize import (
    normalize_conflict_policy,
    normalize_copy_move_backend,
    normalize_delete_backend,
    normalize_dispatch_mode,
    normalize_queue_view_mode,
    normalize_shortcut_behavior,
    normalize_terminal_launcher,
    normalize_terminal_startup_position,
)

from . import normalize
from .registry import SettingsRegistry


class OpsDefaultSettingsMixin(SettingsDomainBase, SettingsRegistry):
    """Persist operation defaults and file-open tool preferences."""

    @property
    def default_copy_move_backend(self) -> str:
        return normalize_copy_move_backend(
            self._storage.value(
                self.DEFAULT_COPY_MOVE_BACKEND_KEY,
                self.DEFAULT_COPY_MOVE_BACKEND,
            )
        )

    @default_copy_move_backend.setter
    def default_copy_move_backend(self, backend: str) -> None:
        self._storage.set_value(
            self.DEFAULT_COPY_MOVE_BACKEND_KEY,
            normalize_copy_move_backend(backend),
        )

    @property
    def default_delete_backend(self) -> str:
        return normalize_delete_backend(
            self._storage.value(
                self.DEFAULT_DELETE_BACKEND_KEY,
                self.DEFAULT_DELETE_BACKEND,
            )
        )

    @default_delete_backend.setter
    def default_delete_backend(self, backend: str) -> None:
        self._storage.set_value(
            self.DEFAULT_DELETE_BACKEND_KEY,
            normalize_delete_backend(backend),
        )

    @property
    def default_archive_packer_backend(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.DEFAULT_ARCHIVE_PACKER_BACKEND_KEY,
                self.DEFAULT_DEFAULT_ARCHIVE_PACKER_BACKEND,
            ),
            fallback=self.DEFAULT_DEFAULT_ARCHIVE_PACKER_BACKEND,
        )

    @default_archive_packer_backend.setter
    def default_archive_packer_backend(self, backend: str) -> None:
        self._storage.set_value(
            self.DEFAULT_ARCHIVE_PACKER_BACKEND_KEY,
            normalize.normalize_text(
                backend,
                fallback=self.DEFAULT_DEFAULT_ARCHIVE_PACKER_BACKEND,
            ),
        )

    @property
    def default_archive_unpacker_backend(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.DEFAULT_ARCHIVE_UNPACKER_BACKEND_KEY,
                self.DEFAULT_DEFAULT_ARCHIVE_UNPACKER_BACKEND,
            ),
            fallback=self.DEFAULT_DEFAULT_ARCHIVE_UNPACKER_BACKEND,
        )

    @default_archive_unpacker_backend.setter
    def default_archive_unpacker_backend(self, backend: str) -> None:
        self._storage.set_value(
            self.DEFAULT_ARCHIVE_UNPACKER_BACKEND_KEY,
            normalize.normalize_text(
                backend,
                fallback=self.DEFAULT_DEFAULT_ARCHIVE_UNPACKER_BACKEND,
            ),
        )

    @property
    def default_operation_dispatch_mode(self) -> str:
        return normalize_dispatch_mode(
            self._storage.value(
                self.DEFAULT_OPERATION_DISPATCH_MODE_KEY,
                self.DEFAULT_OPERATION_DISPATCH_MODE,
            )
        )

    @default_operation_dispatch_mode.setter
    def default_operation_dispatch_mode(self, mode: str) -> None:
        self._storage.set_value(
            self.DEFAULT_OPERATION_DISPATCH_MODE_KEY,
            normalize_dispatch_mode(mode),
        )

    @property
    def default_operation_conflict_policy(self) -> str:
        return normalize_conflict_policy(
            self._storage.value(
                self.DEFAULT_OPERATION_CONFLICT_POLICY_KEY,
                self.DEFAULT_OPERATION_CONFLICT_POLICY,
            )
        )

    @default_operation_conflict_policy.setter
    def default_operation_conflict_policy(self, policy: str) -> None:
        self._storage.set_value(
            self.DEFAULT_OPERATION_CONFLICT_POLICY_KEY,
            normalize_conflict_policy(policy),
        )

    @property
    def operation_shortcut_behavior(self) -> str:
        return normalize_shortcut_behavior(
            self._storage.value(
                self.OPERATION_SHORTCUT_BEHAVIOR_KEY,
                self.DEFAULT_OPERATION_SHORTCUT_BEHAVIOR,
            )
        )

    @operation_shortcut_behavior.setter
    def operation_shortcut_behavior(self, behavior: str) -> None:
        self._storage.set_value(
            self.OPERATION_SHORTCUT_BEHAVIOR_KEY,
            normalize_shortcut_behavior(behavior),
        )

    @property
    def operation_queue_view_mode(self) -> str:
        return normalize_queue_view_mode(
            self._storage.value(
                self.OPERATION_QUEUE_VIEW_MODE_KEY,
                self.DEFAULT_OPERATION_QUEUE_VIEW_MODE,
            )
        )

    @operation_queue_view_mode.setter
    def operation_queue_view_mode(self, mode: str) -> None:
        self._storage.set_value(
            self.OPERATION_QUEUE_VIEW_MODE_KEY,
            normalize_queue_view_mode(mode),
        )

    @property
    def default_editor_executable(self) -> str:
        return normalize.normalize_windows_path_text(
            self._storage.value(
                self.DEFAULT_EDITOR_EXECUTABLE_KEY,
                self.DEFAULT_DEFAULT_EDITOR_EXECUTABLE,
            ),
            fallback=self.DEFAULT_DEFAULT_EDITOR_EXECUTABLE,
        )

    @default_editor_executable.setter
    def default_editor_executable(self, value: str) -> None:
        self._storage.set_value(
            self.DEFAULT_EDITOR_EXECUTABLE_KEY,
            normalize.normalize_windows_path_text(
                value, fallback=self.DEFAULT_DEFAULT_EDITOR_EXECUTABLE
            ),
        )

    @property
    def default_viewer_executable(self) -> str:
        return normalize.normalize_windows_path_text(
            self._storage.value(
                self.DEFAULT_VIEWER_EXECUTABLE_KEY,
                self.DEFAULT_DEFAULT_VIEWER_EXECUTABLE,
            ),
            fallback=self.DEFAULT_DEFAULT_VIEWER_EXECUTABLE,
        )

    @default_viewer_executable.setter
    def default_viewer_executable(self, value: str) -> None:
        self._storage.set_value(
            self.DEFAULT_VIEWER_EXECUTABLE_KEY,
            normalize.normalize_windows_path_text(
                value, fallback=self.DEFAULT_DEFAULT_VIEWER_EXECUTABLE
            ),
        )

    @property
    def default_terminal_launcher(self) -> str:
        return normalize_terminal_launcher(
            self._storage.value(
                self.DEFAULT_TERMINAL_LAUNCHER_KEY,
                self.DEFAULT_DEFAULT_TERMINAL_LAUNCHER,
            )
        )

    @default_terminal_launcher.setter
    def default_terminal_launcher(self, value: str) -> None:
        self._storage.set_value(
            self.DEFAULT_TERMINAL_LAUNCHER_KEY,
            normalize_terminal_launcher(
                value,
                fallback=self.DEFAULT_DEFAULT_TERMINAL_LAUNCHER,
            ),
        )

    @property
    def comspec_terminal_executable(self) -> str:
        return normalize.normalize_windows_path_text(
            self._storage.value(
                self.COMSPEC_TERMINAL_EXECUTABLE_KEY,
                self.DEFAULT_COMSPEC_TERMINAL_EXECUTABLE,
            ),
            fallback=self.DEFAULT_COMSPEC_TERMINAL_EXECUTABLE,
        )

    @comspec_terminal_executable.setter
    def comspec_terminal_executable(self, value: str) -> None:
        self._storage.set_value(
            self.COMSPEC_TERMINAL_EXECUTABLE_KEY,
            normalize.normalize_windows_path_text(
                value,
                fallback=self.DEFAULT_COMSPEC_TERMINAL_EXECUTABLE,
            ),
        )

    @property
    def comspec_terminal_open_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.COMSPEC_TERMINAL_OPEN_ARGS_TEMPLATE_KEY,
                self.DEFAULT_COMSPEC_TERMINAL_OPEN_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_COMSPEC_TERMINAL_OPEN_ARGS_TEMPLATE,
        )

    @comspec_terminal_open_args_template.setter
    def comspec_terminal_open_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.COMSPEC_TERMINAL_OPEN_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_COMSPEC_TERMINAL_OPEN_ARGS_TEMPLATE,
            ),
        )

    @property
    def comspec_terminal_command_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.COMSPEC_TERMINAL_COMMAND_ARGS_TEMPLATE_KEY,
                self.DEFAULT_COMSPEC_TERMINAL_COMMAND_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_COMSPEC_TERMINAL_COMMAND_ARGS_TEMPLATE,
        )

    @comspec_terminal_command_args_template.setter
    def comspec_terminal_command_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.COMSPEC_TERMINAL_COMMAND_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_COMSPEC_TERMINAL_COMMAND_ARGS_TEMPLATE,
            ),
        )

    @property
    def comspec_terminal_startup_position(self) -> str:
        return normalize_terminal_startup_position(
            self._storage.value(
                self.COMSPEC_TERMINAL_STARTUP_POSITION_KEY,
                self.DEFAULT_COMSPEC_TERMINAL_STARTUP_POSITION,
            )
        )

    @comspec_terminal_startup_position.setter
    def comspec_terminal_startup_position(self, value: str) -> None:
        self._storage.set_value(
            self.COMSPEC_TERMINAL_STARTUP_POSITION_KEY,
            normalize_terminal_startup_position(
                value,
                fallback=self.DEFAULT_COMSPEC_TERMINAL_STARTUP_POSITION,
            ),
        )

    @property
    def pwsh_terminal_executable(self) -> str:
        return normalize.normalize_windows_path_text(
            self._storage.value(
                self.PWSH_TERMINAL_EXECUTABLE_KEY,
                self.DEFAULT_PWSH_TERMINAL_EXECUTABLE,
            ),
            fallback=self.DEFAULT_PWSH_TERMINAL_EXECUTABLE,
        )

    @pwsh_terminal_executable.setter
    def pwsh_terminal_executable(self, value: str) -> None:
        self._storage.set_value(
            self.PWSH_TERMINAL_EXECUTABLE_KEY,
            normalize.normalize_windows_path_text(
                value,
                fallback=self.DEFAULT_PWSH_TERMINAL_EXECUTABLE,
            ),
        )

    @property
    def pwsh_terminal_open_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.PWSH_TERMINAL_OPEN_ARGS_TEMPLATE_KEY,
                self.DEFAULT_PWSH_TERMINAL_OPEN_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_PWSH_TERMINAL_OPEN_ARGS_TEMPLATE,
        )

    @pwsh_terminal_open_args_template.setter
    def pwsh_terminal_open_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.PWSH_TERMINAL_OPEN_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_PWSH_TERMINAL_OPEN_ARGS_TEMPLATE,
            ),
        )

    @property
    def pwsh_terminal_command_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.PWSH_TERMINAL_COMMAND_ARGS_TEMPLATE_KEY,
                self.DEFAULT_PWSH_TERMINAL_COMMAND_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_PWSH_TERMINAL_COMMAND_ARGS_TEMPLATE,
        )

    @pwsh_terminal_command_args_template.setter
    def pwsh_terminal_command_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.PWSH_TERMINAL_COMMAND_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_PWSH_TERMINAL_COMMAND_ARGS_TEMPLATE,
            ),
        )

    @property
    def pwsh_terminal_startup_position(self) -> str:
        return normalize_terminal_startup_position(
            self._storage.value(
                self.PWSH_TERMINAL_STARTUP_POSITION_KEY,
                self.DEFAULT_PWSH_TERMINAL_STARTUP_POSITION,
            )
        )

    @pwsh_terminal_startup_position.setter
    def pwsh_terminal_startup_position(self, value: str) -> None:
        self._storage.set_value(
            self.PWSH_TERMINAL_STARTUP_POSITION_KEY,
            normalize_terminal_startup_position(
                value,
                fallback=self.DEFAULT_PWSH_TERMINAL_STARTUP_POSITION,
            ),
        )

    @property
    def powershell5_terminal_executable(self) -> str:
        return normalize.normalize_windows_path_text(
            self._storage.value(
                self.POWERSHELL5_TERMINAL_EXECUTABLE_KEY,
                self.DEFAULT_POWERSHELL5_TERMINAL_EXECUTABLE,
            ),
            fallback=self.DEFAULT_POWERSHELL5_TERMINAL_EXECUTABLE,
        )

    @powershell5_terminal_executable.setter
    def powershell5_terminal_executable(self, value: str) -> None:
        self._storage.set_value(
            self.POWERSHELL5_TERMINAL_EXECUTABLE_KEY,
            normalize.normalize_windows_path_text(
                value,
                fallback=self.DEFAULT_POWERSHELL5_TERMINAL_EXECUTABLE,
            ),
        )

    @property
    def powershell5_terminal_open_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.POWERSHELL5_TERMINAL_OPEN_ARGS_TEMPLATE_KEY,
                self.DEFAULT_POWERSHELL5_TERMINAL_OPEN_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_POWERSHELL5_TERMINAL_OPEN_ARGS_TEMPLATE,
        )

    @powershell5_terminal_open_args_template.setter
    def powershell5_terminal_open_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.POWERSHELL5_TERMINAL_OPEN_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_POWERSHELL5_TERMINAL_OPEN_ARGS_TEMPLATE,
            ),
        )

    @property
    def powershell5_terminal_command_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.POWERSHELL5_TERMINAL_COMMAND_ARGS_TEMPLATE_KEY,
                self.DEFAULT_POWERSHELL5_TERMINAL_COMMAND_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_POWERSHELL5_TERMINAL_COMMAND_ARGS_TEMPLATE,
        )

    @powershell5_terminal_command_args_template.setter
    def powershell5_terminal_command_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.POWERSHELL5_TERMINAL_COMMAND_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_POWERSHELL5_TERMINAL_COMMAND_ARGS_TEMPLATE,
            ),
        )

    @property
    def powershell5_terminal_startup_position(self) -> str:
        return normalize_terminal_startup_position(
            self._storage.value(
                self.POWERSHELL5_TERMINAL_STARTUP_POSITION_KEY,
                self.DEFAULT_POWERSHELL5_TERMINAL_STARTUP_POSITION,
            )
        )

    @powershell5_terminal_startup_position.setter
    def powershell5_terminal_startup_position(self, value: str) -> None:
        self._storage.set_value(
            self.POWERSHELL5_TERMINAL_STARTUP_POSITION_KEY,
            normalize_terminal_startup_position(
                value,
                fallback=self.DEFAULT_POWERSHELL5_TERMINAL_STARTUP_POSITION,
            ),
        )

    @property
    def windows_terminal_executable(self) -> str:
        return normalize.normalize_windows_path_text(
            self._storage.value(
                self.WINDOWS_TERMINAL_EXECUTABLE_KEY,
                self.DEFAULT_WINDOWS_TERMINAL_EXECUTABLE,
            ),
            fallback=self.DEFAULT_WINDOWS_TERMINAL_EXECUTABLE,
        )

    @windows_terminal_executable.setter
    def windows_terminal_executable(self, value: str) -> None:
        self._storage.set_value(
            self.WINDOWS_TERMINAL_EXECUTABLE_KEY,
            normalize.normalize_windows_path_text(
                value,
                fallback=self.DEFAULT_WINDOWS_TERMINAL_EXECUTABLE,
            ),
        )

    @property
    def windows_terminal_open_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.WINDOWS_TERMINAL_OPEN_ARGS_TEMPLATE_KEY,
                self.DEFAULT_WINDOWS_TERMINAL_OPEN_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_WINDOWS_TERMINAL_OPEN_ARGS_TEMPLATE,
        )

    @windows_terminal_open_args_template.setter
    def windows_terminal_open_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.WINDOWS_TERMINAL_OPEN_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_WINDOWS_TERMINAL_OPEN_ARGS_TEMPLATE,
            ),
        )

    @property
    def windows_terminal_command_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.WINDOWS_TERMINAL_COMMAND_ARGS_TEMPLATE_KEY,
                self.DEFAULT_WINDOWS_TERMINAL_COMMAND_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_WINDOWS_TERMINAL_COMMAND_ARGS_TEMPLATE,
        )

    @windows_terminal_command_args_template.setter
    def windows_terminal_command_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.WINDOWS_TERMINAL_COMMAND_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_WINDOWS_TERMINAL_COMMAND_ARGS_TEMPLATE,
            ),
        )

    @property
    def windows_terminal_startup_position(self) -> str:
        return normalize_terminal_startup_position(
            self._storage.value(
                self.WINDOWS_TERMINAL_STARTUP_POSITION_KEY,
                self.DEFAULT_WINDOWS_TERMINAL_STARTUP_POSITION,
            )
        )

    @windows_terminal_startup_position.setter
    def windows_terminal_startup_position(self, value: str) -> None:
        self._storage.set_value(
            self.WINDOWS_TERMINAL_STARTUP_POSITION_KEY,
            normalize_terminal_startup_position(
                value,
                fallback=self.DEFAULT_WINDOWS_TERMINAL_STARTUP_POSITION,
            ),
        )

    @property
    def alacritty_terminal_executable(self) -> str:
        return normalize.normalize_windows_path_text(
            self._storage.value(
                self.ALACRITTY_TERMINAL_EXECUTABLE_KEY,
                self.DEFAULT_ALACRITTY_TERMINAL_EXECUTABLE,
            ),
            fallback=self.DEFAULT_ALACRITTY_TERMINAL_EXECUTABLE,
        )

    @alacritty_terminal_executable.setter
    def alacritty_terminal_executable(self, value: str) -> None:
        self._storage.set_value(
            self.ALACRITTY_TERMINAL_EXECUTABLE_KEY,
            normalize.normalize_windows_path_text(
                value,
                fallback=self.DEFAULT_ALACRITTY_TERMINAL_EXECUTABLE,
            ),
        )

    @property
    def alacritty_terminal_open_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.ALACRITTY_TERMINAL_OPEN_ARGS_TEMPLATE_KEY,
                self.DEFAULT_ALACRITTY_TERMINAL_OPEN_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_ALACRITTY_TERMINAL_OPEN_ARGS_TEMPLATE,
        )

    @alacritty_terminal_open_args_template.setter
    def alacritty_terminal_open_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.ALACRITTY_TERMINAL_OPEN_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_ALACRITTY_TERMINAL_OPEN_ARGS_TEMPLATE,
            ),
        )

    @property
    def alacritty_terminal_command_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.ALACRITTY_TERMINAL_COMMAND_ARGS_TEMPLATE_KEY,
                self.DEFAULT_ALACRITTY_TERMINAL_COMMAND_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_ALACRITTY_TERMINAL_COMMAND_ARGS_TEMPLATE,
        )

    @alacritty_terminal_command_args_template.setter
    def alacritty_terminal_command_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.ALACRITTY_TERMINAL_COMMAND_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_ALACRITTY_TERMINAL_COMMAND_ARGS_TEMPLATE,
            ),
        )

    @property
    def alacritty_terminal_startup_position(self) -> str:
        return normalize_terminal_startup_position(
            self._storage.value(
                self.ALACRITTY_TERMINAL_STARTUP_POSITION_KEY,
                self.DEFAULT_ALACRITTY_TERMINAL_STARTUP_POSITION,
            )
        )

    @alacritty_terminal_startup_position.setter
    def alacritty_terminal_startup_position(self, value: str) -> None:
        self._storage.set_value(
            self.ALACRITTY_TERMINAL_STARTUP_POSITION_KEY,
            normalize_terminal_startup_position(
                value,
                fallback=self.DEFAULT_ALACRITTY_TERMINAL_STARTUP_POSITION,
            ),
        )

    @property
    def wezterm_terminal_executable(self) -> str:
        return normalize.normalize_windows_path_text(
            self._storage.value(
                self.WEZTERM_TERMINAL_EXECUTABLE_KEY,
                self.DEFAULT_WEZTERM_TERMINAL_EXECUTABLE,
            ),
            fallback=self.DEFAULT_WEZTERM_TERMINAL_EXECUTABLE,
        )

    @wezterm_terminal_executable.setter
    def wezterm_terminal_executable(self, value: str) -> None:
        self._storage.set_value(
            self.WEZTERM_TERMINAL_EXECUTABLE_KEY,
            normalize.normalize_windows_path_text(
                value,
                fallback=self.DEFAULT_WEZTERM_TERMINAL_EXECUTABLE,
            ),
        )

    @property
    def wezterm_terminal_open_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.WEZTERM_TERMINAL_OPEN_ARGS_TEMPLATE_KEY,
                self.DEFAULT_WEZTERM_TERMINAL_OPEN_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_WEZTERM_TERMINAL_OPEN_ARGS_TEMPLATE,
        )

    @wezterm_terminal_open_args_template.setter
    def wezterm_terminal_open_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.WEZTERM_TERMINAL_OPEN_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_WEZTERM_TERMINAL_OPEN_ARGS_TEMPLATE,
            ),
        )

    @property
    def wezterm_terminal_command_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.WEZTERM_TERMINAL_COMMAND_ARGS_TEMPLATE_KEY,
                self.DEFAULT_WEZTERM_TERMINAL_COMMAND_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_WEZTERM_TERMINAL_COMMAND_ARGS_TEMPLATE,
        )

    @wezterm_terminal_command_args_template.setter
    def wezterm_terminal_command_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.WEZTERM_TERMINAL_COMMAND_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_WEZTERM_TERMINAL_COMMAND_ARGS_TEMPLATE,
            ),
        )

    @property
    def wezterm_terminal_startup_position(self) -> str:
        return normalize_terminal_startup_position(
            self._storage.value(
                self.WEZTERM_TERMINAL_STARTUP_POSITION_KEY,
                self.DEFAULT_WEZTERM_TERMINAL_STARTUP_POSITION,
            )
        )

    @wezterm_terminal_startup_position.setter
    def wezterm_terminal_startup_position(self, value: str) -> None:
        self._storage.set_value(
            self.WEZTERM_TERMINAL_STARTUP_POSITION_KEY,
            normalize_terminal_startup_position(
                value,
                fallback=self.DEFAULT_WEZTERM_TERMINAL_STARTUP_POSITION,
            ),
        )

    @property
    def file_open_overrides_json(self) -> str:
        return normalize.normalize_overrides_json(
            self._storage.value(
                self.FILE_OPEN_OVERRIDES_JSON_KEY,
                self.DEFAULT_FILE_OPEN_OVERRIDES_JSON,
            ),
            fallback=self.DEFAULT_FILE_OPEN_OVERRIDES_JSON,
        )

    @file_open_overrides_json.setter
    def file_open_overrides_json(self, value: str) -> None:
        self._storage.set_value(
            self.FILE_OPEN_OVERRIDES_JSON_KEY,
            normalize.normalize_overrides_json(
                value,
                fallback=self.DEFAULT_FILE_OPEN_OVERRIDES_JSON,
            ),
        )

    @property
    def total_commander_executable(self) -> str:
        return normalize.normalize_windows_path_text(
            self._storage.value(
                self.TOTAL_COMMANDER_EXECUTABLE_KEY,
                self.DEFAULT_TOTAL_COMMANDER_EXECUTABLE,
            ),
            fallback=self.DEFAULT_TOTAL_COMMANDER_EXECUTABLE,
        )

    @total_commander_executable.setter
    def total_commander_executable(self, value: str) -> None:
        self._storage.set_value(
            self.TOTAL_COMMANDER_EXECUTABLE_KEY,
            normalize.normalize_windows_path_text(
                value,
                fallback=self.DEFAULT_TOTAL_COMMANDER_EXECUTABLE,
            ),
        )

    @property
    def total_commander_source_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.TOTAL_COMMANDER_SOURCE_ARGS_TEMPLATE_KEY,
                self.DEFAULT_TOTAL_COMMANDER_SOURCE_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_TOTAL_COMMANDER_SOURCE_ARGS_TEMPLATE,
        )

    @total_commander_source_args_template.setter
    def total_commander_source_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.TOTAL_COMMANDER_SOURCE_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_TOTAL_COMMANDER_SOURCE_ARGS_TEMPLATE,
            ),
        )

    @property
    def total_commander_source_target_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.TOTAL_COMMANDER_SOURCE_TARGET_ARGS_TEMPLATE_KEY,
                self.DEFAULT_TOTAL_COMMANDER_SOURCE_TARGET_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_TOTAL_COMMANDER_SOURCE_TARGET_ARGS_TEMPLATE,
        )

    @total_commander_source_target_args_template.setter
    def total_commander_source_target_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.TOTAL_COMMANDER_SOURCE_TARGET_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_TOTAL_COMMANDER_SOURCE_TARGET_ARGS_TEMPLATE,
            ),
        )

    @property
    def double_commander_executable(self) -> str:
        return normalize.normalize_windows_path_text(
            self._storage.value(
                self.DOUBLE_COMMANDER_EXECUTABLE_KEY,
                self.DEFAULT_DOUBLE_COMMANDER_EXECUTABLE,
            ),
            fallback=self.DEFAULT_DOUBLE_COMMANDER_EXECUTABLE,
        )

    @double_commander_executable.setter
    def double_commander_executable(self, value: str) -> None:
        self._storage.set_value(
            self.DOUBLE_COMMANDER_EXECUTABLE_KEY,
            normalize.normalize_windows_path_text(
                value,
                fallback=self.DEFAULT_DOUBLE_COMMANDER_EXECUTABLE,
            ),
        )

    @property
    def double_commander_source_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.DOUBLE_COMMANDER_SOURCE_ARGS_TEMPLATE_KEY,
                self.DEFAULT_DOUBLE_COMMANDER_SOURCE_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_DOUBLE_COMMANDER_SOURCE_ARGS_TEMPLATE,
        )

    @double_commander_source_args_template.setter
    def double_commander_source_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.DOUBLE_COMMANDER_SOURCE_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_DOUBLE_COMMANDER_SOURCE_ARGS_TEMPLATE,
            ),
        )

    @property
    def double_commander_source_target_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.DOUBLE_COMMANDER_SOURCE_TARGET_ARGS_TEMPLATE_KEY,
                self.DEFAULT_DOUBLE_COMMANDER_SOURCE_TARGET_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_DOUBLE_COMMANDER_SOURCE_TARGET_ARGS_TEMPLATE,
        )

    @double_commander_source_target_args_template.setter
    def double_commander_source_target_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.DOUBLE_COMMANDER_SOURCE_TARGET_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_DOUBLE_COMMANDER_SOURCE_TARGET_ARGS_TEMPLATE,
            ),
        )

    @property
    def everything_executable(self) -> str:
        return normalize.normalize_windows_path_text(
            self._storage.value(
                self.EVERYTHING_EXECUTABLE_KEY,
                self.DEFAULT_EVERYTHING_EXECUTABLE,
            ),
            fallback=self.DEFAULT_EVERYTHING_EXECUTABLE,
        )

    @everything_executable.setter
    def everything_executable(self, value: str) -> None:
        self._storage.set_value(
            self.EVERYTHING_EXECUTABLE_KEY,
            normalize.normalize_windows_path_text(
                value,
                fallback=self.DEFAULT_EVERYTHING_EXECUTABLE,
            ),
        )

    @property
    def use_everything_sdk_for_folder_sizes(self) -> bool:
        return bool(
            self._storage.value(
                self.USE_EVERYTHING_SDK_FOR_FOLDER_SIZES_KEY,
                self.DEFAULT_USE_EVERYTHING_SDK_FOR_FOLDER_SIZES,
            )
        )

    @use_everything_sdk_for_folder_sizes.setter
    def use_everything_sdk_for_folder_sizes(self, value: bool) -> None:
        self._storage.set_value(
            self.USE_EVERYTHING_SDK_FOR_FOLDER_SIZES_KEY,
            bool(value),
        )

    @property
    def file_list_mouse_selection_mode(self) -> str:
        return normalize.normalize_choice(
            self._storage.value(
                self.FILE_LIST_MOUSE_SELECTION_MODE_KEY,
                self.DEFAULT_FILE_LIST_MOUSE_SELECTION_MODE,
            ),
            fallback=self.DEFAULT_FILE_LIST_MOUSE_SELECTION_MODE,
            allowed=self.ALLOWED_FILE_LIST_MOUSE_SELECTION_MODES,
        )

    @file_list_mouse_selection_mode.setter
    def file_list_mouse_selection_mode(self, value: str) -> None:
        self._storage.set_value(
            self.FILE_LIST_MOUSE_SELECTION_MODE_KEY,
            normalize.normalize_choice(
                value,
                fallback=self.DEFAULT_FILE_LIST_MOUSE_SELECTION_MODE,
                allowed=self.ALLOWED_FILE_LIST_MOUSE_SELECTION_MODES,
            ),
        )

    @property
    def auto_calculate_dir_sizes_on_space(self) -> bool:
        return bool(
            self._storage.value(
                self.AUTO_CALCULATE_DIR_SIZES_ON_SPACE_KEY,
                self.DEFAULT_AUTO_CALCULATE_DIR_SIZES_ON_SPACE,
            )
        )

    @auto_calculate_dir_sizes_on_space.setter
    def auto_calculate_dir_sizes_on_space(self, value: bool) -> None:
        self._storage.set_value(
            self.AUTO_CALCULATE_DIR_SIZES_ON_SPACE_KEY,
            bool(value),
        )

    @property
    def auto_calculate_dir_sizes_before_copy_move(self) -> bool:
        return bool(
            self._storage.value(
                self.AUTO_CALCULATE_DIR_SIZES_BEFORE_COPY_MOVE_KEY,
                self.DEFAULT_AUTO_CALCULATE_DIR_SIZES_BEFORE_COPY_MOVE,
            )
        )

    @auto_calculate_dir_sizes_before_copy_move.setter
    def auto_calculate_dir_sizes_before_copy_move(self, value: bool) -> None:
        self._storage.set_value(
            self.AUTO_CALCULATE_DIR_SIZES_BEFORE_COPY_MOVE_KEY,
            bool(value),
        )

    @property
    def auto_calculate_dir_sizes_before_archive(self) -> bool:
        return bool(
            self._storage.value(
                self.AUTO_CALCULATE_DIR_SIZES_BEFORE_ARCHIVE_KEY,
                self.DEFAULT_AUTO_CALCULATE_DIR_SIZES_BEFORE_ARCHIVE,
            )
        )

    @auto_calculate_dir_sizes_before_archive.setter
    def auto_calculate_dir_sizes_before_archive(self, value: bool) -> None:
        self._storage.set_value(
            self.AUTO_CALCULATE_DIR_SIZES_BEFORE_ARCHIVE_KEY,
            bool(value),
        )

    @property
    def seven_zip_executable(self) -> str:
        return normalize.normalize_windows_path_text(
            self._storage.value(
                self.SEVEN_ZIP_EXECUTABLE_KEY,
                self.DEFAULT_SEVEN_ZIP_EXECUTABLE,
            ),
            fallback=self.DEFAULT_SEVEN_ZIP_EXECUTABLE,
        )

    @seven_zip_executable.setter
    def seven_zip_executable(self, value: str) -> None:
        self._storage.set_value(
            self.SEVEN_ZIP_EXECUTABLE_KEY,
            normalize.normalize_windows_path_text(
                value,
                fallback=self.DEFAULT_SEVEN_ZIP_EXECUTABLE,
            ),
        )

    @property
    def seven_zip_pack_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.SEVEN_ZIP_PACK_ARGS_TEMPLATE_KEY,
                self.DEFAULT_SEVEN_ZIP_PACK_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_SEVEN_ZIP_PACK_ARGS_TEMPLATE,
        )

    @seven_zip_pack_args_template.setter
    def seven_zip_pack_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.SEVEN_ZIP_PACK_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_SEVEN_ZIP_PACK_ARGS_TEMPLATE,
            ),
        )

    @property
    def seven_zip_extract_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.SEVEN_ZIP_EXTRACT_ARGS_TEMPLATE_KEY,
                self.DEFAULT_SEVEN_ZIP_EXTRACT_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_SEVEN_ZIP_EXTRACT_ARGS_TEMPLATE,
        )

    @seven_zip_extract_args_template.setter
    def seven_zip_extract_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.SEVEN_ZIP_EXTRACT_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_SEVEN_ZIP_EXTRACT_ARGS_TEMPLATE,
            ),
        )

    @property
    def winrar_executable(self) -> str:
        return normalize.normalize_windows_path_text(
            self._storage.value(
                self.WINRAR_EXECUTABLE_KEY,
                self.DEFAULT_WINRAR_EXECUTABLE,
            ),
            fallback=self.DEFAULT_WINRAR_EXECUTABLE,
        )

    @winrar_executable.setter
    def winrar_executable(self, value: str) -> None:
        self._storage.set_value(
            self.WINRAR_EXECUTABLE_KEY,
            normalize.normalize_windows_path_text(
                value,
                fallback=self.DEFAULT_WINRAR_EXECUTABLE,
            ),
        )

    @property
    def winrar_pack_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.WINRAR_PACK_ARGS_TEMPLATE_KEY,
                self.DEFAULT_WINRAR_PACK_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_WINRAR_PACK_ARGS_TEMPLATE,
        )

    @winrar_pack_args_template.setter
    def winrar_pack_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.WINRAR_PACK_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_WINRAR_PACK_ARGS_TEMPLATE,
            ),
        )

    @property
    def winrar_extract_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.WINRAR_EXTRACT_ARGS_TEMPLATE_KEY,
                self.DEFAULT_WINRAR_EXTRACT_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_WINRAR_EXTRACT_ARGS_TEMPLATE,
        )

    @winrar_extract_args_template.setter
    def winrar_extract_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.WINRAR_EXTRACT_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value,
                fallback=self.DEFAULT_WINRAR_EXTRACT_ARGS_TEMPLATE,
            ),
        )
