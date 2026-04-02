"""Behavior and visibility settings for the UI domain."""

from __future__ import annotations

from threep_commons.settings import SettingsDomainBase

from . import normalize
from .registry import SettingsRegistry


class UiBehaviorSettingsMixin(SettingsDomainBase, SettingsRegistry):
    """Persist behavior, visibility, and context-tool preferences."""

    @property
    def new_context_mode(self) -> str:
        value = str(self._storage.value(self.NEW_CONTEXT_MODE_KEY, "clone_active_path"))
        mode = value.strip().lower()
        if mode not in self.ALLOWED_NEW_CONTEXT_MODES:
            return "clone_active_path"
        return mode

    @new_context_mode.setter
    def new_context_mode(self, mode: str) -> None:
        normalized = str(mode).strip().lower()
        if normalized not in self.ALLOWED_NEW_CONTEXT_MODES:
            normalized = "clone_active_path"
        self._storage.set_value(self.NEW_CONTEXT_MODE_KEY, normalized)

    @property
    def show_hidden_default(self) -> bool:
        return normalize.normalize_bool(
            self._storage.value(self.SHOW_HIDDEN_DEFAULT_KEY, True)
        )

    @show_hidden_default.setter
    def show_hidden_default(self, enabled: bool) -> None:
        self._storage.set_value(self.SHOW_HIDDEN_DEFAULT_KEY, bool(enabled))

    @property
    def show_system_files(self) -> bool:
        return normalize.normalize_bool(
            self._storage.value(
                self.SHOW_SYSTEM_FILES_KEY,
                self.DEFAULT_SHOW_SYSTEM_FILES,
            )
        )

    @show_system_files.setter
    def show_system_files(self, enabled: bool) -> None:
        self._storage.set_value(self.SHOW_SYSTEM_FILES_KEY, bool(enabled))

    @property
    def show_root_dropdown(self) -> bool:
        return normalize.normalize_bool(
            self._storage.value(self.SHOW_ROOT_DROPDOWN_KEY, False)
        )

    @show_root_dropdown.setter
    def show_root_dropdown(self, enabled: bool) -> None:
        self._storage.set_value(self.SHOW_ROOT_DROPDOWN_KEY, bool(enabled))

    @property
    def show_status_bar(self) -> bool:
        return normalize.normalize_bool(
            self._storage.value(
                self.SHOW_STATUS_BAR_KEY,
                self.DEFAULT_SHOW_STATUS_BAR,
            )
        )

    @show_status_bar.setter
    def show_status_bar(self, enabled: bool) -> None:
        self._storage.set_value(self.SHOW_STATUS_BAR_KEY, bool(enabled))

    @property
    def show_storage_overview_status_row(self) -> bool:
        return normalize.normalize_bool(
            self._storage.value(
                self.SHOW_STORAGE_OVERVIEW_STATUS_ROW_KEY,
                self.DEFAULT_SHOW_STORAGE_OVERVIEW_STATUS_ROW,
            )
        )

    @show_storage_overview_status_row.setter
    def show_storage_overview_status_row(self, enabled: bool) -> None:
        self._storage.set_value(
            self.SHOW_STORAGE_OVERVIEW_STATUS_ROW_KEY, bool(enabled)
        )

    @property
    def column_width_auto_align_mode(self) -> str:
        value = str(
            self._storage.value(
                self.COLUMN_WIDTH_AUTO_ALIGN_MODE_KEY,
                self.DEFAULT_COLUMN_WIDTH_AUTO_ALIGN_MODE,
            )
        )
        mode = value.strip().lower()
        if mode not in self.ALLOWED_COLUMN_WIDTH_AUTO_ALIGN_MODES:
            return self.DEFAULT_COLUMN_WIDTH_AUTO_ALIGN_MODE
        return mode

    @column_width_auto_align_mode.setter
    def column_width_auto_align_mode(self, mode: str) -> None:
        normalized = str(mode).strip().lower()
        if normalized not in self.ALLOWED_COLUMN_WIDTH_AUTO_ALIGN_MODES:
            normalized = self.DEFAULT_COLUMN_WIDTH_AUTO_ALIGN_MODE
        self._storage.set_value(self.COLUMN_WIDTH_AUTO_ALIGN_MODE_KEY, normalized)

    @property
    def directories_sort_mode(self) -> str:
        value = str(
            self._storage.value(
                self.DIRECTORIES_SORT_MODE_KEY,
                self.DEFAULT_DIRECTORIES_SORT_MODE,
            )
        )
        mode = value.strip().lower()
        if mode not in self.ALLOWED_DIRECTORIES_SORT_MODES:
            return self.DEFAULT_DIRECTORIES_SORT_MODE
        return mode

    @directories_sort_mode.setter
    def directories_sort_mode(self, mode: str) -> None:
        normalized = str(mode).strip().lower()
        if normalized not in self.ALLOWED_DIRECTORIES_SORT_MODES:
            normalized = self.DEFAULT_DIRECTORIES_SORT_MODE
        self._storage.set_value(self.DIRECTORIES_SORT_MODE_KEY, normalized)

    @property
    def show_parent_dir_at_drive_root(self) -> bool:
        return normalize.normalize_bool(
            self._storage.value(
                self.SHOW_PARENT_DIR_AT_DRIVE_ROOT_KEY,
                self.DEFAULT_SHOW_PARENT_DIR_AT_DRIVE_ROOT,
            )
        )

    @show_parent_dir_at_drive_root.setter
    def show_parent_dir_at_drive_root(self, enabled: bool) -> None:
        self._storage.set_value(
            self.SHOW_PARENT_DIR_AT_DRIVE_ROOT_KEY,
            bool(enabled),
        )

    @property
    def show_square_brackets_around_directories(self) -> bool:
        return normalize.normalize_bool(
            self._storage.value(
                self.SHOW_SQUARE_BRACKETS_AROUND_DIRECTORIES_KEY,
                self.DEFAULT_SHOW_SQUARE_BRACKETS_AROUND_DIRECTORIES,
            )
        )

    @show_square_brackets_around_directories.setter
    def show_square_brackets_around_directories(self, enabled: bool) -> None:
        self._storage.set_value(
            self.SHOW_SQUARE_BRACKETS_AROUND_DIRECTORIES_KEY,
            bool(enabled),
        )

    @property
    def append_directory_backslash(self) -> bool:
        return normalize.normalize_bool(
            self._storage.value(
                self.APPEND_DIRECTORY_BACKSLASH_KEY,
                self.DEFAULT_APPEND_DIRECTORY_BACKSLASH,
            )
        )

    @append_directory_backslash.setter
    def append_directory_backslash(self, enabled: bool) -> None:
        self._storage.set_value(self.APPEND_DIRECTORY_BACKSLASH_KEY, bool(enabled))

    @property
    def name_sort_method(self) -> str:
        value = str(
            self._storage.value(
                self.NAME_SORT_METHOD_KEY,
                self.DEFAULT_NAME_SORT_METHOD,
            )
        )
        mode = value.strip().lower()
        if mode not in self.ALLOWED_NAME_SORT_METHODS:
            return self.DEFAULT_NAME_SORT_METHOD
        return mode

    @name_sort_method.setter
    def name_sort_method(self, mode: str) -> None:
        normalized = str(mode).strip().lower()
        if normalized not in self.ALLOWED_NAME_SORT_METHODS:
            normalized = self.DEFAULT_NAME_SORT_METHOD
        self._storage.set_value(self.NAME_SORT_METHOD_KEY, normalized)

    @property
    def autofit_columns(self) -> bool:
        return normalize.normalize_bool(
            self._storage.value(
                self.AUTOFIT_COLUMNS_KEY,
                self.DEFAULT_AUTOFIT_COLUMNS,
            )
        )

    @autofit_columns.setter
    def autofit_columns(self, enabled: bool) -> None:
        self._storage.set_value(self.AUTOFIT_COLUMNS_KEY, bool(enabled))

    @property
    def show_refresh_button(self) -> bool:
        return normalize.normalize_bool(
            self._storage.value(self.SHOW_REFRESH_BUTTON_KEY, True)
        )

    @show_refresh_button.setter
    def show_refresh_button(self, enabled: bool) -> None:
        self._storage.set_value(self.SHOW_REFRESH_BUTTON_KEY, bool(enabled))

    @property
    def show_root_buttons(self) -> bool:
        return normalize.normalize_bool(
            self._storage.value(self.SHOW_ROOT_BUTTONS_KEY, True)
        )

    @show_root_buttons.setter
    def show_root_buttons(self, enabled: bool) -> None:
        self._storage.set_value(self.SHOW_ROOT_BUTTONS_KEY, bool(enabled))

    @property
    def show_address_bar(self) -> bool:
        return normalize.normalize_bool(
            self._storage.value(self.SHOW_ADDRESS_BAR_KEY, True)
        )

    @show_address_bar.setter
    def show_address_bar(self, enabled: bool) -> None:
        self._storage.set_value(self.SHOW_ADDRESS_BAR_KEY, bool(enabled))

    @property
    def show_breadcrumb_bar(self) -> bool:
        return normalize.normalize_bool(
            self._storage.value(
                self.SHOW_BREADCRUMB_BAR_KEY,
                self.DEFAULT_SHOW_BREADCRUMB_BAR,
            )
        )

    @show_breadcrumb_bar.setter
    def show_breadcrumb_bar(self, enabled: bool) -> None:
        self._storage.set_value(self.SHOW_BREADCRUMB_BAR_KEY, bool(enabled))

    @property
    def show_navigation_buttons(self) -> bool:
        return normalize.normalize_bool(
            self._storage.value(self.SHOW_NAVIGATION_BUTTONS_KEY, True)
        )

    @show_navigation_buttons.setter
    def show_navigation_buttons(self, enabled: bool) -> None:
        self._storage.set_value(self.SHOW_NAVIGATION_BUTTONS_KEY, bool(enabled))

    @property
    def show_history_button(self) -> bool:
        return normalize.normalize_bool(
            self._storage.value(
                self.SHOW_HISTORY_BUTTON_KEY,
                self.DEFAULT_SHOW_HISTORY_BUTTON,
            )
        )

    @show_history_button.setter
    def show_history_button(self, enabled: bool) -> None:
        self._storage.set_value(self.SHOW_HISTORY_BUTTON_KEY, bool(enabled))

    @property
    def show_bookmarks_button(self) -> bool:
        return normalize.normalize_bool(
            self._storage.value(
                self.SHOW_BOOKMARKS_BUTTON_KEY,
                self.DEFAULT_SHOW_BOOKMARKS_BUTTON,
            )
        )

    @show_bookmarks_button.setter
    def show_bookmarks_button(self, enabled: bool) -> None:
        self._storage.set_value(self.SHOW_BOOKMARKS_BUTTON_KEY, bool(enabled))

    @property
    def show_tab_bar(self) -> bool:
        return normalize.normalize_bool(
            self._storage.value(
                self.SHOW_TAB_BAR_KEY,
                self.DEFAULT_SHOW_TAB_BAR,
            )
        )

    @show_tab_bar.setter
    def show_tab_bar(self, enabled: bool) -> None:
        self._storage.set_value(self.SHOW_TAB_BAR_KEY, bool(enabled))

    @property
    def show_tab_close_buttons(self) -> bool:
        return normalize.normalize_bool(
            self._storage.value(
                self.SHOW_TAB_CLOSE_BUTTONS_KEY,
                self.DEFAULT_SHOW_TAB_CLOSE_BUTTONS,
            )
        )

    @show_tab_close_buttons.setter
    def show_tab_close_buttons(self, enabled: bool) -> None:
        self._storage.set_value(self.SHOW_TAB_CLOSE_BUTTONS_KEY, bool(enabled))

    @property
    def default_tab_position(self) -> str:
        value = str(
            self._storage.value(
                self.DEFAULT_TAB_POSITION_KEY,
                self.DEFAULT_DEFAULT_TAB_POSITION,
            )
        )
        mode = value.strip().lower()
        if mode not in self.ALLOWED_DEFAULT_TAB_POSITION_MODES:
            return self.DEFAULT_DEFAULT_TAB_POSITION
        return mode

    @default_tab_position.setter
    def default_tab_position(self, mode: str) -> None:
        normalized = str(mode).strip().lower()
        if normalized not in self.ALLOWED_DEFAULT_TAB_POSITION_MODES:
            normalized = self.DEFAULT_DEFAULT_TAB_POSITION
        self._storage.set_value(self.DEFAULT_TAB_POSITION_KEY, normalized)

    @property
    def horizontal_tab_width_mode(self) -> str:
        """Return the current width policy for horizontal side tabs."""

        return normalize.normalize_horizontal_tab_width_mode(
            self._storage.value(
                self.HORIZONTAL_TAB_WIDTH_MODE_KEY,
                self.DEFAULT_HORIZONTAL_TAB_WIDTH_MODE,
            ),
            fallback=self.DEFAULT_HORIZONTAL_TAB_WIDTH_MODE,
            allowed_modes=self.ALLOWED_HORIZONTAL_TAB_WIDTH_MODES,
        )

    @horizontal_tab_width_mode.setter
    def horizontal_tab_width_mode(self, mode: str) -> None:
        self._storage.set_value(
            self.HORIZONTAL_TAB_WIDTH_MODE_KEY,
            normalize.normalize_horizontal_tab_width_mode(
                mode,
                fallback=self.DEFAULT_HORIZONTAL_TAB_WIDTH_MODE,
                allowed_modes=self.ALLOWED_HORIZONTAL_TAB_WIDTH_MODES,
            ),
        )

    @property
    def horizontal_tab_fixed_width_px(self) -> int:
        """Return the fixed width used for horizontal side tabs."""

        return normalize.normalize_horizontal_tab_fixed_width_px(
            self._storage.value(
                self.HORIZONTAL_TAB_FIXED_WIDTH_PX_KEY,
                self.DEFAULT_HORIZONTAL_TAB_FIXED_WIDTH_PX,
            ),
            fallback=self.DEFAULT_HORIZONTAL_TAB_FIXED_WIDTH_PX,
            minimum=self.MIN_HORIZONTAL_TAB_FIXED_WIDTH_PX,
            maximum=self.MAX_HORIZONTAL_TAB_FIXED_WIDTH_PX,
        )

    @horizontal_tab_fixed_width_px.setter
    def horizontal_tab_fixed_width_px(self, width_px: int) -> None:
        self._storage.set_value(
            self.HORIZONTAL_TAB_FIXED_WIDTH_PX_KEY,
            normalize.normalize_horizontal_tab_fixed_width_px(
                width_px,
                fallback=self.DEFAULT_HORIZONTAL_TAB_FIXED_WIDTH_PX,
                minimum=self.MIN_HORIZONTAL_TAB_FIXED_WIDTH_PX,
                maximum=self.MAX_HORIZONTAL_TAB_FIXED_WIDTH_PX,
            ),
        )

    @property
    def standard_tab_width_mode(self) -> str:
        """Return the current width policy for standard tab positions."""

        return normalize.normalize_standard_tab_width_mode(
            self._storage.value(
                self.STANDARD_TAB_WIDTH_MODE_KEY,
                self.DEFAULT_STANDARD_TAB_WIDTH_MODE,
            ),
            fallback=self.DEFAULT_STANDARD_TAB_WIDTH_MODE,
            allowed_modes=self.ALLOWED_STANDARD_TAB_WIDTH_MODES,
        )

    @standard_tab_width_mode.setter
    def standard_tab_width_mode(self, mode: str) -> None:
        self._storage.set_value(
            self.STANDARD_TAB_WIDTH_MODE_KEY,
            normalize.normalize_standard_tab_width_mode(
                mode,
                fallback=self.DEFAULT_STANDARD_TAB_WIDTH_MODE,
                allowed_modes=self.ALLOWED_STANDARD_TAB_WIDTH_MODES,
            ),
        )

    @property
    def standard_tab_fixed_width_px(self) -> int:
        """Return the fixed width used by standard tab positions."""

        return normalize.normalize_standard_tab_fixed_width_px(
            self._storage.value(
                self.STANDARD_TAB_FIXED_WIDTH_PX_KEY,
                self.DEFAULT_STANDARD_TAB_FIXED_WIDTH_PX,
            ),
            fallback=self.DEFAULT_STANDARD_TAB_FIXED_WIDTH_PX,
            minimum=self.MIN_STANDARD_TAB_FIXED_WIDTH_PX,
            maximum=self.MAX_STANDARD_TAB_FIXED_WIDTH_PX,
        )

    @standard_tab_fixed_width_px.setter
    def standard_tab_fixed_width_px(self, width_px: int) -> None:
        self._storage.set_value(
            self.STANDARD_TAB_FIXED_WIDTH_PX_KEY,
            normalize.normalize_standard_tab_fixed_width_px(
                width_px,
                fallback=self.DEFAULT_STANDARD_TAB_FIXED_WIDTH_PX,
                minimum=self.MIN_STANDARD_TAB_FIXED_WIDTH_PX,
                maximum=self.MAX_STANDARD_TAB_FIXED_WIDTH_PX,
            ),
        )

    @property
    def file_icon_mode(self) -> str:
        value = str(
            self._storage.value(
                self.FILE_ICON_MODE_KEY,
                self.DEFAULT_FILE_ICON_MODE,
            )
        )
        mode = value.strip().lower()
        if mode not in self.ALLOWED_FILE_ICON_MODES:
            return self.DEFAULT_FILE_ICON_MODE
        return mode

    @file_icon_mode.setter
    def file_icon_mode(self, mode: str) -> None:
        normalized = str(mode).strip().lower()
        if normalized not in self.ALLOWED_FILE_ICON_MODES:
            normalized = self.DEFAULT_FILE_ICON_MODE
        self._storage.set_value(self.FILE_ICON_MODE_KEY, normalized)

    @property
    def dim_hidden_entries(self) -> bool:
        return normalize.normalize_bool(
            self._storage.value(
                self.DIM_HIDDEN_ENTRIES_KEY,
                self.DEFAULT_DIM_HIDDEN_ENTRIES,
            )
        )

    @dim_hidden_entries.setter
    def dim_hidden_entries(self, enabled: bool) -> None:
        self._storage.set_value(self.DIM_HIDDEN_ENTRIES_KEY, bool(enabled))

    @property
    def file_icon_size_px(self) -> int:
        return normalize.normalize_positive_int(
            self._storage.value(
                self.FILE_ICON_SIZE_PX_KEY,
                self.DEFAULT_FILE_ICON_SIZE_PX,
            ),
            fallback=self.DEFAULT_FILE_ICON_SIZE_PX,
            minimum=self.MIN_FILE_ICON_SIZE_PX,
            maximum=self.MAX_FILE_ICON_SIZE_PX,
        )

    @file_icon_size_px.setter
    def file_icon_size_px(self, value: int) -> None:
        self._storage.set_value(
            self.FILE_ICON_SIZE_PX_KEY,
            normalize.normalize_positive_int(
                value,
                fallback=self.DEFAULT_FILE_ICON_SIZE_PX,
                minimum=self.MIN_FILE_ICON_SIZE_PX,
                maximum=self.MAX_FILE_ICON_SIZE_PX,
            ),
        )

    @property
    def file_icon_padding_horizontal(self) -> int:
        return normalize.normalize_positive_int(
            self._storage.value(
                self.FILE_ICON_PADDING_HORIZONTAL_KEY,
                self.DEFAULT_FILE_ICON_PADDING_HORIZONTAL,
            ),
            fallback=self.DEFAULT_FILE_ICON_PADDING_HORIZONTAL,
            minimum=self.MIN_FILE_ICON_PADDING_PX,
            maximum=self.MAX_FILE_ICON_PADDING_PX,
        )

    @file_icon_padding_horizontal.setter
    def file_icon_padding_horizontal(self, value: int) -> None:
        self._storage.set_value(
            self.FILE_ICON_PADDING_HORIZONTAL_KEY,
            normalize.normalize_positive_int(
                value,
                fallback=self.DEFAULT_FILE_ICON_PADDING_HORIZONTAL,
                minimum=self.MIN_FILE_ICON_PADDING_PX,
                maximum=self.MAX_FILE_ICON_PADDING_PX,
            ),
        )

    @property
    def file_icon_padding_vertical(self) -> int:
        return normalize.normalize_positive_int(
            self._storage.value(
                self.FILE_ICON_PADDING_VERTICAL_KEY,
                self.DEFAULT_FILE_ICON_PADDING_VERTICAL,
            ),
            fallback=self.DEFAULT_FILE_ICON_PADDING_VERTICAL,
            minimum=self.MIN_FILE_ICON_PADDING_PX,
            maximum=self.MAX_FILE_ICON_PADDING_PX,
        )

    @file_icon_padding_vertical.setter
    def file_icon_padding_vertical(self, value: int) -> None:
        self._storage.set_value(
            self.FILE_ICON_PADDING_VERTICAL_KEY,
            normalize.normalize_positive_int(
                value,
                fallback=self.DEFAULT_FILE_ICON_PADDING_VERTICAL,
                minimum=self.MIN_FILE_ICON_PADDING_PX,
                maximum=self.MAX_FILE_ICON_PADDING_PX,
            ),
        )

    @property
    def context_immediate_child_scan_cap(self) -> int:
        return normalize.normalize_positive_int(
            self._storage.value(
                self.CONTEXT_IMMEDIATE_CHILD_SCAN_CAP_KEY,
                self.DEFAULT_CONTEXT_IMMEDIATE_CHILD_SCAN_CAP,
            ),
            fallback=self.DEFAULT_CONTEXT_IMMEDIATE_CHILD_SCAN_CAP,
            minimum=1,
            maximum=10_000,
        )

    @context_immediate_child_scan_cap.setter
    def context_immediate_child_scan_cap(self, value: int) -> None:
        self._storage.set_value(
            self.CONTEXT_IMMEDIATE_CHILD_SCAN_CAP_KEY,
            normalize.normalize_positive_int(
                value,
                fallback=self.DEFAULT_CONTEXT_IMMEDIATE_CHILD_SCAN_CAP,
                minimum=1,
                maximum=10_000,
            ),
        )

    @property
    def context_tool_code_editor_exe_path(self) -> str:
        return normalize.normalize_windows_path_text(
            self._storage.value(
                self.CONTEXT_TOOL_CODE_EDITOR_EXE_PATH_KEY,
                self.DEFAULT_CONTEXT_TOOL_CODE_EDITOR_EXE_PATH,
            ),
            fallback=self.DEFAULT_CONTEXT_TOOL_CODE_EDITOR_EXE_PATH,
        )

    @context_tool_code_editor_exe_path.setter
    def context_tool_code_editor_exe_path(self, value: str) -> None:
        self._storage.set_value(
            self.CONTEXT_TOOL_CODE_EDITOR_EXE_PATH_KEY,
            normalize.normalize_windows_path_text(
                value, fallback=self.DEFAULT_CONTEXT_TOOL_CODE_EDITOR_EXE_PATH
            ),
        )

    @property
    def context_tool_code_editor_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.CONTEXT_TOOL_CODE_EDITOR_ARGS_TEMPLATE_KEY,
                self.DEFAULT_CONTEXT_TOOL_CODE_EDITOR_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_CONTEXT_TOOL_CODE_EDITOR_ARGS_TEMPLATE,
        )

    @context_tool_code_editor_args_template.setter
    def context_tool_code_editor_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.CONTEXT_TOOL_CODE_EDITOR_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value, fallback=self.DEFAULT_CONTEXT_TOOL_CODE_EDITOR_ARGS_TEMPLATE
            ),
        )

    @property
    def context_tool_git_gui_exe_path(self) -> str:
        return normalize.normalize_windows_path_text(
            self._storage.value(
                self.CONTEXT_TOOL_GIT_GUI_EXE_PATH_KEY,
                self.DEFAULT_CONTEXT_TOOL_GIT_GUI_EXE_PATH,
            ),
            fallback=self.DEFAULT_CONTEXT_TOOL_GIT_GUI_EXE_PATH,
        )

    @context_tool_git_gui_exe_path.setter
    def context_tool_git_gui_exe_path(self, value: str) -> None:
        self._storage.set_value(
            self.CONTEXT_TOOL_GIT_GUI_EXE_PATH_KEY,
            normalize.normalize_windows_path_text(
                value, fallback=self.DEFAULT_CONTEXT_TOOL_GIT_GUI_EXE_PATH
            ),
        )

    @property
    def context_tool_git_gui_args_template(self) -> str:
        return normalize.normalize_text(
            self._storage.value(
                self.CONTEXT_TOOL_GIT_GUI_ARGS_TEMPLATE_KEY,
                self.DEFAULT_CONTEXT_TOOL_GIT_GUI_ARGS_TEMPLATE,
            ),
            fallback=self.DEFAULT_CONTEXT_TOOL_GIT_GUI_ARGS_TEMPLATE,
        )

    @context_tool_git_gui_args_template.setter
    def context_tool_git_gui_args_template(self, value: str) -> None:
        self._storage.set_value(
            self.CONTEXT_TOOL_GIT_GUI_ARGS_TEMPLATE_KEY,
            normalize.normalize_text(
                value, fallback=self.DEFAULT_CONTEXT_TOOL_GIT_GUI_ARGS_TEMPLATE
            ),
        )
