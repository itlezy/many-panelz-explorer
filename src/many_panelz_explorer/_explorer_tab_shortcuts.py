"""File-list shortcut routing for explorer tabs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6.QtGui import QKeyEvent

    from ._explorer_tab_actions import ExplorerTabActions
    from .explorer_tab import ExplorerTab


class ExplorerTabFileListShortcuts:
    """Route file-list key bindings for one explorer tab."""

    def __init__(
        self,
        *,
        tab: ExplorerTab,
        actions: ExplorerTabActions,
        trigger_window_shortcut: Callable[[str], bool],
        trigger_window_action: Callable[[str], bool],
        handle_keypad_mark_shortcut: Callable[[QKeyEvent], bool],
    ) -> None:
        """Store the owned callbacks and prebuild stable shortcut maps."""

        self._tab = tab
        self._actions = actions
        self._trigger_window_shortcut = trigger_window_shortcut
        self._trigger_window_action = trigger_window_action
        self._handle_keypad_mark_shortcut = handle_keypad_mark_shortcut
        self._window_shortcuts = self._build_window_shortcut_dispatch()
        self._window_actions = self._build_window_action_dispatch()
        self._local_actions = self._build_local_action_dispatch()

    def handle_key(self, key_event: QKeyEvent) -> bool:
        """Handle one file-list key event when it matches a known binding."""

        modifiers = key_event.modifiers()
        key = key_event.key()
        return (
            self._handle_window_shortcut_binding(modifiers, key)
            or self._handle_mark_shortcut_binding(key_event, modifiers, key)
            or self._handle_window_action_binding(modifiers, key)
            or self._handle_local_action_shortcut_binding(modifiers, key)
        )

    def _build_window_shortcut_dispatch(
        self,
    ) -> dict[tuple[Qt.KeyboardModifier, int], str]:
        """Build the map of file-list keys to window-owned shortcuts."""

        return {
            (
                Qt.KeyboardModifier.ControlModifier,
                int(Qt.Key.Key_Tab),
            ): "next_tab_shortcut",
            (
                Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
                int(Qt.Key.Key_Tab),
            ): "previous_tab_shortcut",
            (
                Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
                int(Qt.Key.Key_Backtab),
            ): "previous_tab_shortcut",
            (
                Qt.KeyboardModifier.ControlModifier,
                int(Qt.Key.Key_PageDown),
            ): "next_tab_alias_shortcut",
            (
                Qt.KeyboardModifier.ControlModifier,
                int(Qt.Key.Key_PageUp),
            ): "previous_tab_alias_shortcut",
            (
                Qt.KeyboardModifier.ControlModifier,
                int(Qt.Key.Key_D),
            ): "bookmarks_hotlist_shortcut",
            (
                Qt.KeyboardModifier.ControlModifier,
                int(Qt.Key.Key_I),
            ): "sync_target_panel_path_shortcut",
            (
                Qt.KeyboardModifier.ControlModifier,
                int(Qt.Key.Key_U),
            ): "exchange_panel_paths_shortcut",
            (
                Qt.KeyboardModifier.NoModifier,
                int(Qt.Key.Key_F3),
            ): "list_files_shortcut",
            (
                Qt.KeyboardModifier.AltModifier,
                int(Qt.Key.Key_F3),
            ): "alt_list_files_shortcut",
            (
                Qt.KeyboardModifier.NoModifier,
                int(Qt.Key.Key_F4),
            ): "edit_files_shortcut",
            (
                Qt.KeyboardModifier.ShiftModifier,
                int(Qt.Key.Key_F4),
            ): "new_file_shortcut",
            (
                Qt.KeyboardModifier.NoModifier,
                int(Qt.Key.Key_F7),
            ): "create_directory_shortcut",
            (
                Qt.KeyboardModifier.NoModifier,
                int(Qt.Key.Key_F9),
            ): "terminal_here_shortcut",
        }

    def _build_window_action_dispatch(
        self,
    ) -> dict[tuple[Qt.KeyboardModifier, int], str]:
        """Build the map of file-list keys to window-owned actions."""

        return {
            (
                Qt.KeyboardModifier.NoModifier,
                int(Qt.Key.Key_F5),
            ): "copy_to_target_action",
            (
                Qt.KeyboardModifier.NoModifier,
                int(Qt.Key.Key_F6),
            ): "move_to_target_action",
            (
                Qt.KeyboardModifier.NoModifier,
                int(Qt.Key.Key_F8),
            ): "delete_selection_action",
            (
                Qt.KeyboardModifier.NoModifier,
                int(Qt.Key.Key_Delete),
            ): "delete_selection_action",
        }

    def _build_local_action_dispatch(
        self,
    ) -> dict[tuple[Qt.KeyboardModifier, int], Callable[[], bool]]:
        """Build the map of file-list keys to tab-local actions."""

        return {
            (
                Qt.KeyboardModifier.AltModifier,
                int(Qt.Key.Key_F7),
            ): lambda: self._run_shortcut_action(self._tab.launch_everything_search),
            (
                Qt.KeyboardModifier.AltModifier,
                int(Qt.Key.Key_F9),
            ): lambda: self._run_shortcut_action(self._tab.extract_supported_archive),
            (
                Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ShiftModifier,
                int(Qt.Key.Key_F9),
            ): lambda: self._run_shortcut_action(self._tab.test_supported_archives),
            (
                Qt.KeyboardModifier.ControlModifier,
                int(Qt.Key.Key_L),
            ): lambda: self._run_shortcut_action(
                self._tab.calculate_selected_or_current_folder_sizes
            ),
            (
                Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ShiftModifier,
                int(Qt.Key.Key_Return),
            ): lambda: self._run_shortcut_action(
                self._tab.calculate_visible_folder_sizes
            ),
            (
                Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ShiftModifier,
                int(Qt.Key.Key_Enter),
            ): lambda: self._run_shortcut_action(
                self._tab.calculate_visible_folder_sizes
            ),
            (
                Qt.KeyboardModifier.AltModifier,
                int(Qt.Key.Key_Return),
            ): lambda: self._run_shortcut_action(
                self._tab.show_properties_selected_or_current
            ),
            (
                Qt.KeyboardModifier.AltModifier,
                int(Qt.Key.Key_Enter),
            ): lambda: self._run_shortcut_action(
                self._tab.show_properties_selected_or_current
            ),
            (
                Qt.KeyboardModifier.ControlModifier,
                int(Qt.Key.Key_F3),
            ): lambda: self._run_sort_shortcut(0),
            (
                Qt.KeyboardModifier.ControlModifier,
                int(Qt.Key.Key_F4),
            ): lambda: self._run_sort_shortcut(1),
            (
                Qt.KeyboardModifier.ControlModifier,
                int(Qt.Key.Key_F5),
            ): lambda: self._run_sort_shortcut(3),
            (
                Qt.KeyboardModifier.ControlModifier,
                int(Qt.Key.Key_F6),
            ): lambda: self._run_sort_shortcut(2),
            (
                Qt.KeyboardModifier.ShiftModifier,
                int(Qt.Key.Key_F5),
            ): lambda: self._run_shortcut_action(
                self._tab.copy_selected_or_current_to_current_directory
            ),
            (
                Qt.KeyboardModifier.ShiftModifier,
                int(Qt.Key.Key_F6),
            ): lambda: self._run_shortcut_action(self._tab.rename_selected_or_current),
            (
                Qt.KeyboardModifier.ShiftModifier,
                int(Qt.Key.Key_F7),
            ): lambda: self._run_shortcut_action(self._tab.create_directory_in_target),
        }

    def _handle_window_shortcut_binding(
        self,
        modifiers: Qt.KeyboardModifier,
        key: int,
    ) -> bool:
        """Forward matching keys to window-owned shortcuts."""

        shortcut_name = self._window_shortcuts.get((modifiers, key))
        if shortcut_name is None:
            return False
        return self._trigger_window_shortcut(shortcut_name)

    def _handle_mark_shortcut_binding(
        self,
        key_event: QKeyEvent,
        modifiers: Qt.KeyboardModifier,
        key: int,
    ) -> bool:
        """Handle mark, selection, and context-menu file-list shortcuts."""

        if modifiers == Qt.KeyboardModifier.NoModifier and key == int(
            Qt.Key.Key_Insert
        ):
            self._actions.toggle_current_item_selection_and_advance()
            return True
        if modifiers == Qt.KeyboardModifier.NoModifier and key == int(Qt.Key.Key_Space):
            self._actions.toggle_current_item_selection()
            return True
        if self._handle_keypad_mark_shortcut(key_event):
            return True
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == int(
            Qt.Key.Key_A
        ):
            self._actions.select_all_items()
            return True
        if modifiers == Qt.KeyboardModifier.ShiftModifier and key == int(
            Qt.Key.Key_F10
        ):
            self._actions.open_context_menu_from_keyboard()
            return True
        return False

    def _handle_window_action_binding(
        self,
        modifiers: Qt.KeyboardModifier,
        key: int,
    ) -> bool:
        """Forward matching keys to window-owned actions."""

        action_name = self._window_actions.get((modifiers, key))
        if action_name is None:
            return False
        return self._trigger_window_action(action_name)

    def _handle_local_action_shortcut_binding(
        self,
        modifiers: Qt.KeyboardModifier,
        key: int,
    ) -> bool:
        """Handle tab-local file-list shortcuts."""

        handler = self._local_actions.get((modifiers, key))
        if handler is None:
            return False
        return handler()

    def _run_shortcut_action(self, action: Callable[[], None]) -> bool:
        """Run one local shortcut action and report the key as handled."""

        action()
        return True

    def _run_sort_shortcut(self, column: int) -> bool:
        """Run one sort shortcut and report the key as handled."""

        self._tab.sort_by_column(column)
        return True
