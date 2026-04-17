"""Panel widget rebuild helpers for explorer windows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QWidget

from ...explorer_tab import ExplorerTab
from ...panel_widget import PanelWidget
from ...runtime_trace import trace_span
from .layout import WindowLayoutCoordinator

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from ...window import ExplorerWindow
    from .panel_columns import WindowPanelColumnSyncCoordinator
    from .state_types import PanelRows, PanelState, TabsState


def _clear_layout(window: ExplorerWindow) -> None:
    """Delete the current central layout widgets."""

    while window.central_layout.count() > 0:
        item = window.central_layout.takeAt(0)
        if item is None:
            continue
        widget = item.widget()
        if widget is not None:
            widget.hide()
            widget.deleteLater()


def _build_rows_widget(
    window: ExplorerWindow,
    panel_widgets: dict[int, PanelWidget],
    rows: PanelRows,
) -> QWidget | None:
    """Build the nested splitter widget for the current rows."""

    if not rows:
        return None
    if len(rows) == 1:
        return _build_row_widget(window, panel_widgets, rows[0])

    splitter = QSplitter(Qt.Orientation.Vertical, window)
    for row in rows:
        row_widget = _build_row_widget(window, panel_widgets, row)
        splitter.addWidget(row_widget if row_widget is not None else QWidget())
    splitter.setChildrenCollapsible(False)
    splitter.setSizes([1000] * len(rows))
    return splitter


def _build_row_widget(
    window: ExplorerWindow,
    panel_widgets: dict[int, PanelWidget],
    row: list[int],
) -> QWidget | None:
    """Build a single horizontal splitter row."""

    if not row:
        return None
    if len(row) == 1:
        panel = panel_widgets.get(row[0])
        return panel if panel is not None else QWidget()

    splitter = QSplitter(Qt.Orientation.Horizontal, window)
    for panel_id in row:
        panel = panel_widgets.get(panel_id)
        splitter.addWidget(panel if panel is not None else QWidget())
    splitter.setChildrenCollapsible(False)
    splitter.setSizes([1000] * len(row))
    return splitter


class WindowPanelRebuildCoordinator:
    """Rebuild panel widgets and apply presentation preferences."""

    def __init__(
        self,
        window: ExplorerWindow,
        column_sync_coordinator: WindowPanelColumnSyncCoordinator,
    ) -> None:
        """Store rebuild dependencies tied to the owning window."""

        self.window = window
        self.column_sync_coordinator = column_sync_coordinator

    def rebuild_from_tree(
        self,
        tabs_state: TabsState,
        preferred_active_panel: int | None,
        *,
        panel_activated_callback: Callable[[int], Callable[[], None]],
        panel_empty_callback: Callable[[int], Callable[[], None]],
        set_active_panel: Callable[[int], None],
    ) -> None:
        """Rebuild panel widgets from the current normalized row layout."""

        normalized_rows = self._normalized_layout_rows()
        panel_ids = WindowLayoutCoordinator.ordered_panel_ids(normalized_rows)
        with trace_span(
            "window.rebuild_panels",
            "layout",
            args={
                "panel_count": len(panel_ids),
                "restoring_saved_active_panel": preferred_active_panel is not None,
            },
        ):
            self.window.layout_rows = normalized_rows
            self.window.layout_coordinator.sync_panel_tree_from_rows()

            new_panel_widgets: dict[int, PanelWidget] = {}
            for panel_id in panel_ids:
                panel = self._build_panel_widget(
                    panel_id,
                    tabs_state.get(panel_id),
                    panel_activated_callback=panel_activated_callback,
                    panel_empty_callback=panel_empty_callback,
                )
                new_panel_widgets[panel_id] = panel

            self.window.panel_widgets = new_panel_widgets

            root_widget = _build_rows_widget(
                self.window,
                self.window.panel_widgets,
                self.window.layout_rows,
            )
            if root_widget is None:
                root_widget = QWidget()

            _clear_layout(self.window)
            self.window.central_layout.addWidget(root_widget)

            target_active = self._resolved_active_panel_id(preferred_active_panel)
            if target_active is not None:
                set_active_panel(target_active)
            else:
                self.window.update_pane_visuals()

    def _normalized_layout_rows(self) -> PanelRows:
        """Return normalized layout rows, ensuring at least one panel exists."""

        normalized_rows = self.window.layout_coordinator.normalize_rows(
            self.window.layout_rows
        )
        if normalized_rows:
            return normalized_rows
        return [[1]]

    def _build_panel_widget(
        self,
        panel_id: int,
        panel_state: PanelState | None,
        *,
        panel_activated_callback: Callable[[int], Callable[[], None]],
        panel_empty_callback: Callable[[int], Callable[[], None]],
    ) -> PanelWidget:
        """Create and restore one panel widget for the given identifier."""

        with trace_span(
            "panel.build",
            "layout",
            args={
                "panel_id": panel_id,
                "has_saved_state": panel_state is not None,
            },
        ):
            panel = PanelWidget(
                panel_id=panel_id,
                default_path=self._resolved_seed_path(
                    self.window.preferences_coordinator.initial_path
                ),
                show_hidden=self.window.preferences_coordinator.show_hidden_enabled,
                show_root_dropdown=(
                    self.window.preferences_coordinator.show_root_dropdown_enabled
                ),
                show_tab_close_buttons=(
                    self.window.preferences_coordinator.show_tab_close_buttons_enabled
                ),
                file_list_size_formatter=(
                    self.window.preferences_coordinator.format_file_list_bytes
                ),
                properties_size_formatter=(
                    self.window.preferences_coordinator.format_properties_bytes
                ),
                roots_provider=self.window.roots_provider,
                parent=self.window,
            )
            panel.enable_right_click_row_selection = (
                self.window.preferences_coordinator.enable_right_click_row_selection
            )
            panel.set_keypad_mark_scope(
                self.window.preferences_coordinator.keypad_mark_scope
            )
            self._connect_panel_signals(
                panel_id,
                panel,
                panel_activated_callback=panel_activated_callback,
                panel_empty_callback=panel_empty_callback,
            )
            self._restore_panel_state(panel, panel_state)
            self._apply_panel_preferences(panel)
            return panel

    def _connect_panel_signals(
        self,
        panel_id: int,
        panel: PanelWidget,
        *,
        panel_activated_callback: Callable[[int], Callable[[], None]],
        panel_empty_callback: Callable[[int], Callable[[], None]],
    ) -> None:
        """Connect panel signals used by window-level coordinators."""

        panel.activated.connect(panel_activated_callback(panel_id))
        panel.current_context_changed.connect(self.window.update_pane_visuals)
        panel.column_widths_sync_requested.connect(
            self.column_sync_coordinator.panel_widths_sync_callback(panel_id)
        )
        panel.became_empty.connect(panel_empty_callback(panel_id))
        panel.set_closed_tab_recorder(
            self.window.panels_coordinator.closed_tab_recorder(panel_id)
        )
        panel.state_coordinator.set_column_width_auto_align_mode(
            self.window.preferences_coordinator.column_width_auto_align_mode
        )

    def _restore_panel_state(
        self,
        panel: PanelWidget,
        panel_state: PanelState | None,
    ) -> None:
        """Restore persisted tabs for a panel, or seed a fresh tab when absent."""

        if panel_state is not None:
            panel.state_coordinator.restore_state(panel_state)
            return
        panel.add_tab(
            self._resolved_seed_path(self.window.preferences_coordinator.initial_path)
        )

    def _apply_panel_preferences(self, panel: PanelWidget) -> None:
        """Apply the current window preference presentation settings to a panel."""

        file_list_font, navigation_font = (
            self.window.preferences_coordinator.effective_panel_fonts()
        )
        (
            active_color_hex,
            active_intensity_percent,
            target_color_hex,
            target_intensity_percent,
        ) = self.window.preferences_coordinator.panel_role_visual_preferences()
        (
            show_refresh_button,
            show_root_buttons,
            show_root_dropdown,
            show_address_bar,
            show_breadcrumb_bar,
            show_navigation_buttons,
            show_history_button,
            show_bookmarks_button,
        ) = self.window.preferences_coordinator.panel_toolbar_visibility_preferences()
        (
            horizontal_tab_width_mode,
            horizontal_tab_fixed_width_px,
            standard_tab_width_mode,
            standard_tab_fixed_width_px,
        ) = self.window.preferences_coordinator.panel_tab_width_preferences()
        panel.presentation_coordinator.apply_color_scheme(
            self.window.preferences_coordinator.resolved_color_scheme
        )
        panel.presentation_coordinator.set_role_visual_preferences(
            active_color_hex=active_color_hex,
            active_intensity_percent=active_intensity_percent,
            target_color_hex=target_color_hex,
            target_intensity_percent=target_intensity_percent,
        )
        panel.presentation_coordinator.apply_toolbar_visibility(
            show_refresh_button=show_refresh_button,
            show_root_buttons=show_root_buttons,
            show_root_dropdown=show_root_dropdown,
            show_address_bar=show_address_bar,
            show_breadcrumb_bar=show_breadcrumb_bar,
            show_navigation_buttons=show_navigation_buttons,
            show_history_button=show_history_button,
            show_bookmarks_button=show_bookmarks_button,
        )
        panel.presentation_coordinator.apply_tab_bar_visibility(
            show_tab_bar=self.window.preferences_coordinator.show_tab_bar_enabled
        )
        panel.presentation_coordinator.apply_tab_close_button_visibility(
            show_tab_close_buttons=(
                self.window.preferences_coordinator.show_tab_close_buttons_enabled
            )
        )
        panel.presentation_coordinator.apply_tab_position(
            tab_position_mode=panel.tab_position_mode,
            default_tab_position=self.window.preferences_coordinator.default_tab_position,
            horizontal_tab_width_mode=horizontal_tab_width_mode,
            horizontal_tab_fixed_width_px=horizontal_tab_fixed_width_px,
            standard_tab_width_mode=standard_tab_width_mode,
            standard_tab_fixed_width_px=standard_tab_fixed_width_px,
        )
        panel.presentation_coordinator.apply_font_preferences(
            file_list_font=file_list_font,
            navigation_font=navigation_font,
        )
        panel.enable_right_click_row_selection = (
            self.window.preferences_coordinator.enable_right_click_row_selection
        )
        panel.set_keypad_mark_scope(
            self.window.preferences_coordinator.keypad_mark_scope
        )
        panel.set_show_system_files(
            self.window.preferences_coordinator.show_system_files_enabled
        )
        panel.set_directories_sort_mode(
            self.window.preferences_coordinator.directories_sort_mode
        )
        panel.set_show_parent_dir_at_drive_root(
            self.window.preferences_coordinator.show_parent_dir_at_drive_root_enabled
        )
        panel.set_show_square_brackets_around_directories(
            self.window.preferences_coordinator.show_square_brackets_around_directories_enabled
        )
        panel.set_append_directory_backslash(
            self.window.preferences_coordinator.append_directory_backslash_enabled
        )
        panel.set_name_sort_method(self.window.preferences_coordinator.name_sort_method)
        (
            icon_size_px,
            padding_horizontal_px,
            padding_vertical_px,
        ) = self.window.preferences_coordinator.file_icon_metrics
        panel.set_file_icon_preferences(
            icon_mode=self.window.preferences_coordinator.file_icon_mode,
            dim_hidden_entries=(
                self.window.preferences_coordinator.dim_hidden_entries_enabled
            ),
            icon_size_px=icon_size_px,
            padding_horizontal_px=padding_horizontal_px,
            padding_vertical_px=padding_vertical_px,
        )
        for tab_index in range(panel.tabs.count()):
            tab = panel.tabs.widget(tab_index)
            if isinstance(tab, ExplorerTab):
                tab.set_enable_right_click_row_selection(
                    self.window.preferences_coordinator.enable_right_click_row_selection
                )
                tab.set_keypad_mark_scope(
                    self.window.preferences_coordinator.keypad_mark_scope
                )
                tab.apply_color_scheme(
                    self.window.preferences_coordinator.resolved_color_scheme
                )
        panel.widget_map_coordinator.set_enabled(
            self.window.preferences_coordinator.show_widget_map_enabled
        )

    def _resolved_active_panel_id(
        self,
        preferred_active_panel: int | None,
    ) -> int | None:
        """Return the preferred active panel, or the first available panel."""

        if (
            preferred_active_panel is not None
            and preferred_active_panel in self.window.panel_widgets
        ):
            return preferred_active_panel
        return next(iter(self.window.panel_widgets), None)

    def _resolved_seed_path(self, source_path: Path) -> Path:
        """Resolve the preferred seed path for newly created panel tabs."""

        return self.window.preferences_coordinator.resolve_new_context_path(source_path)
