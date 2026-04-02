"""Presentation and role-visual coordination for a panel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QTabWidget
from threep_commons.fs_paths import display_path_text

from ...color_schemes import (
    ResolvedColorScheme,
    blended_color_hex,
    default_color_scheme,
)
from ...panel_tab_positions import (
    TAB_POSITION_MODE_BOTTOM,
    TAB_POSITION_MODE_LEFT,
    TAB_POSITION_MODE_LEFT_HORIZONTAL,
    TAB_POSITION_MODE_RIGHT,
    TAB_POSITION_MODE_RIGHT_HORIZONTAL,
    normalize_panel_tab_position_mode,
    resolve_tab_position_mode,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6.QtWidgets import QWidget

    from ...panel_widget import PanelWidget


class PanelPresentationCoordinator:
    """Own toolbar visibility, fonts, and panel role styling."""

    def __init__(self, panel: PanelWidget) -> None:
        self.panel = panel
        self._resolved_color_scheme = default_color_scheme()

    def apply_toolbar_visibility(
        self,
        *,
        show_refresh_button: bool,
        show_root_buttons: bool,
        show_root_dropdown: bool,
        show_address_bar: bool,
        show_breadcrumb_bar: bool,
        show_navigation_buttons: bool,
        show_history_button: bool,
        show_bookmarks_button: bool,
    ) -> None:
        dropdown_changed = self.panel.show_root_dropdown != bool(show_root_dropdown)
        self.panel.show_refresh_button = bool(show_refresh_button)
        self.panel.show_root_buttons = bool(show_root_buttons)
        self.panel.show_root_dropdown = bool(show_root_dropdown)
        self.panel.show_address_bar = bool(show_address_bar)
        self.panel.show_breadcrumb_bar = bool(show_breadcrumb_bar)
        self.panel.show_navigation_buttons = bool(show_navigation_buttons)
        self.panel.show_history_button = bool(show_history_button)
        self.panel.show_bookmarks_button = bool(show_bookmarks_button)
        if dropdown_changed:
            self.panel.navigation_coordinator.rebuild_root_controls(
                self.panel.current_path()
            )
        self._sync_toolbar_visibility()
        self.panel.widget_map_coordinator.sync_overlay()

    def apply_tab_bar_visibility(self, *, show_tab_bar: bool) -> None:
        """Show or hide the visible tab strip for this panel."""

        self.panel.show_tab_bar = bool(show_tab_bar)
        self.panel.tabs.tabBar().setVisible(self.panel.show_tab_bar)
        self.panel.widget_map_coordinator.sync_overlay()

    def apply_tab_close_button_visibility(
        self, *, show_tab_close_buttons: bool
    ) -> None:
        """Show or hide tab close buttons for this panel."""

        self.panel.show_tab_close_buttons = bool(show_tab_close_buttons)
        self.panel.tabs.setTabsClosable(self.panel.show_tab_close_buttons)
        self.panel.widget_map_coordinator.sync_overlay()

    def apply_tab_position(
        self,
        *,
        tab_position_mode: str,
        default_tab_position: str,
        horizontal_tab_width_mode: str,
        horizontal_tab_fixed_width_px: int,
        standard_tab_width_mode: str,
        standard_tab_fixed_width_px: int,
    ) -> None:
        """Apply the panel tab-strip position using the current default."""

        self.panel.tab_position_mode = normalize_panel_tab_position_mode(
            tab_position_mode
        )
        resolved_mode = resolve_tab_position_mode(
            self.panel.tab_position_mode,
            default_tab_position=default_tab_position,
        )
        tab_position = QTabWidget.TabPosition.North
        tab_render_mode = "native"
        if resolved_mode == TAB_POSITION_MODE_BOTTOM:
            tab_position = QTabWidget.TabPosition.South
        elif resolved_mode in {
            TAB_POSITION_MODE_LEFT,
            TAB_POSITION_MODE_LEFT_HORIZONTAL,
        }:
            tab_position = QTabWidget.TabPosition.West
            if resolved_mode == TAB_POSITION_MODE_LEFT_HORIZONTAL:
                tab_render_mode = "west_horizontal"
        elif resolved_mode in {
            TAB_POSITION_MODE_RIGHT,
            TAB_POSITION_MODE_RIGHT_HORIZONTAL,
        }:
            tab_position = QTabWidget.TabPosition.East
            if resolved_mode == TAB_POSITION_MODE_RIGHT_HORIZONTAL:
                tab_render_mode = "east_horizontal"

        tab_bar = self.panel.tabs.tabBar()
        self.panel.tabs.setTabPosition(tab_position)
        set_horizontal_tab_width_preferences = getattr(
            tab_bar,
            "set_horizontal_tab_width_preferences",
            None,
        )
        if callable(set_horizontal_tab_width_preferences):
            set_horizontal_tab_width_preferences(
                horizontal_tab_width_mode,
                horizontal_tab_fixed_width_px,
            )
        set_standard_tab_width_preferences = getattr(
            tab_bar,
            "set_standard_tab_width_preferences",
            None,
        )
        if callable(set_standard_tab_width_preferences):
            set_standard_tab_width_preferences(
                standard_tab_width_mode,
                standard_tab_fixed_width_px,
            )
        tab_bar.setProperty("tab_render_mode", tab_render_mode)
        tab_bar.setProperty(
            "left_horizontal_mode",
            tab_render_mode == "west_horizontal",
        )
        tab_bar.setProperty(
            "right_horizontal_mode",
            tab_render_mode == "east_horizontal",
        )
        set_tab_render_mode = getattr(
            tab_bar,
            "set_tab_render_mode",
            None,
        )
        if callable(set_tab_render_mode):
            set_tab_render_mode(tab_render_mode)
        else:
            set_left_horizontal_mode = getattr(
                tab_bar,
                "set_left_horizontal_mode",
                None,
            )
            if callable(set_left_horizontal_mode):
                set_left_horizontal_mode(
                    resolved_mode == TAB_POSITION_MODE_LEFT_HORIZONTAL
                )
        self.panel.widget_map_coordinator.sync_overlay()

    def apply_font_preferences(
        self, *, file_list_font: QFont, navigation_font: QFont
    ) -> None:
        self.panel.file_list_font_value = QFont(file_list_font)
        self.panel.navigation_font_value = QFont(navigation_font)
        self._apply_toolbar_font()
        self._apply_file_list_font()
        self.panel.widget_map_coordinator.sync_overlay()

    def apply_size_formatters(
        self,
        *,
        file_list_size_formatter: Callable[[int], str] | None,
        properties_size_formatter: Callable[[int], str] | None,
    ) -> None:
        self.panel.file_list_size_formatter = (
            file_list_size_formatter or self.panel.default_file_list_size_formatter
        )
        self.panel.properties_size_formatter = (
            properties_size_formatter or self.panel.default_properties_size_formatter
        )
        self._apply_size_formatters_to_tabs()

    def set_role_visual_preferences(
        self,
        *,
        active_color_hex: str,
        active_intensity_percent: int,
        target_color_hex: str,
        target_intensity_percent: int,
    ) -> None:
        active_color = QColor(str(active_color_hex))
        target_color = QColor(str(target_color_hex))
        if active_color.isValid():
            self.panel.active_role_color = active_color
        if target_color.isValid():
            self.panel.target_role_color = target_color
        self.panel.active_role_intensity_percent = self._normalize_percent(
            active_intensity_percent
        )
        self.panel.target_role_intensity_percent = self._normalize_percent(
            target_intensity_percent
        )
        self._apply_visual_role()
        self.panel.widget_map_coordinator.sync_overlay()

    def set_role_visual_state(self, *, is_active: bool, is_target: bool) -> None:
        next_role = "normal"
        if is_active:
            next_role = "active"
        elif is_target:
            next_role = "target"
        if next_role == self.panel.pane_role:
            return
        self.panel.pane_role = next_role
        self._apply_visual_role()
        self.panel.widget_map_coordinator.sync_overlay()

    def sync_toolbar_for_current_tab(self) -> None:
        tab = self.panel.current_tab()
        if tab is None:
            self.panel.back_btn.setEnabled(False)
            self.panel.forward_btn.setEnabled(False)
            self.panel.up_btn.setEnabled(False)
            self.panel.root_btn.setEnabled(False)
            self.panel.refresh_btn.setEnabled(False)
            self.panel.navigation_coordinator.set_address_text_programmatically("")
            self.panel.navigation_coordinator.rebuild_root_controls(None)
            self.panel.widget_map_coordinator.sync_overlay()
            return

        self.panel.back_btn.setEnabled(tab.navigation.can_go_back)
        self.panel.forward_btn.setEnabled(tab.navigation.can_go_forward)
        self.panel.up_btn.setEnabled(True)
        self.panel.root_btn.setEnabled(True)
        self.panel.refresh_btn.setEnabled(True)
        self.panel.navigation_coordinator.set_address_text_programmatically(
            display_path_text(tab.navigation.path)
        )
        self.panel.navigation_coordinator.rebuild_root_controls(tab.navigation.path)
        if self.panel.filter_edit.isVisible():
            tab.navigation.set_inline_filter(self.panel.filter_edit.text())
        self.panel.widget_map_coordinator.sync_overlay()

    def _sync_toolbar_visibility(self) -> None:
        self.panel.refresh_btn.setVisible(self.panel.show_refresh_button)
        self.panel.root_buttons_host.setVisible(self.panel.show_root_buttons)
        self.panel.root_combo.setVisible(self.panel.show_root_dropdown)
        self.panel.address_edit.setVisible(self.panel.show_address_bar)
        self.panel.breadcrumb_host.setVisible(self.panel.show_breadcrumb_bar)
        self.panel.history_btn.setVisible(self.panel.show_history_button)
        self.panel.bookmarks_btn.setVisible(self.panel.show_bookmarks_button)
        for nav_button in self.panel.navigation_buttons:
            nav_button.setVisible(self.panel.show_navigation_buttons)

    def _apply_toolbar_font(self) -> None:
        toolbar_widgets: list[QWidget] = [
            self.panel.refresh_btn,
            self.panel.root_combo,
            self.panel.group_picker_combo,
            self.panel.new_group_btn,
            self.panel.address_edit,
            self.panel.breadcrumb_host,
            self.panel.history_btn,
            self.panel.bookmarks_btn,
            *self.panel.navigation_buttons,
        ]
        for widget in toolbar_widgets:
            widget.setFont(self.panel.navigation_font_value)
        for button in self.panel.root_buttons:
            button.setFont(self.panel.navigation_font_value)
        for button in self.panel.breadcrumb_buttons:
            button.setFont(self.panel.navigation_font_value)

    def _apply_file_list_font(self) -> None:
        for tab in self.panel.iter_all_tabs():
            tab.view.setFont(self.panel.file_list_font_value)

    def _apply_size_formatters_to_tabs(self) -> None:
        for tab in self.panel.iter_all_tabs():
            tab.set_file_size_formatter(self.panel.file_list_size_formatter)
            tab.set_properties_size_formatter(self.panel.properties_size_formatter)

    def apply_color_scheme(self, scheme: ResolvedColorScheme) -> None:
        """Apply the resolved color scheme to panel chrome widgets."""

        self._resolved_color_scheme = scheme
        self._apply_visual_role()
        for tab in self.panel.iter_all_tabs():
            tab.apply_color_scheme(scheme)

    def _apply_visual_role(self) -> None:
        scheme = self._resolved_color_scheme
        if self.panel.pane_role == "active":
            background_color = blended_color_hex(
                scheme.panel_surface_background_hex,
                scheme.active_panel_tint_color_hex,
                overlay_percent=scheme.active_panel_tint_intensity_percent,
            )
        elif self.panel.pane_role == "target":
            background_color = blended_color_hex(
                scheme.panel_surface_background_hex,
                scheme.target_panel_tint_color_hex,
                overlay_percent=scheme.target_panel_tint_intensity_percent,
            )
        else:
            background_color = scheme.panel_surface_background_hex
        panel_object_name = self.panel.objectName()
        style_sheet = (
            f"QWidget#{panel_object_name} {{ "
            f"border: none; "
            f"background-color: {background_color}; "
            f"}} "
            f"QWidget#{panel_object_name} QPushButton {{ "
            f"background-color: {scheme.toolbar_background_hex}; "
            f"color: {scheme.toolbar_text_hex}; "
            f"border: 1px solid {scheme.tab_inactive_background_hex}; "
            f"}} "
            f"QWidget#{panel_object_name} QComboBox {{ "
            f"background-color: {scheme.toolbar_background_hex}; "
            f"color: {scheme.toolbar_text_hex}; "
            f"border: 1px solid {scheme.tab_inactive_background_hex}; "
            f"}} "
            f"QWidget#{panel_object_name} QLineEdit {{ "
            f"background-color: {scheme.toolbar_background_hex}; "
            f"color: {scheme.toolbar_text_hex}; "
            f"border: 1px solid {scheme.tab_inactive_background_hex}; "
            f"}} "
            f"QWidget#{panel_object_name} QTabWidget::pane {{ "
            f"background-color: {scheme.panel_surface_background_hex}; "
            f"border: 1px solid {scheme.tab_inactive_background_hex}; "
            f"}} "
            f"QWidget#{panel_object_name} QTabBar::tab {{ "
            f"background-color: {scheme.tab_inactive_background_hex}; "
            f"color: {scheme.tab_inactive_text_hex}; "
            f"border: 1px solid {scheme.toolbar_background_hex}; "
            f"padding: 4px 8px; "
            f"}} "
            f"QWidget#{panel_object_name} QTabBar::tab:selected {{ "
            f"background-color: {scheme.tab_active_background_hex}; "
            f"color: {scheme.tab_active_text_hex}; "
            f"}}"
        )
        if style_sheet == self.panel.styleSheet():
            return
        self.panel.setStyleSheet(style_sheet)

    def _normalize_percent(self, value: int) -> int:
        if value < 0:
            return 0
        if value > 100:
            return 100
        return int(value)

    def _alpha_from_percent(self, percent: int) -> int:
        normalized = self._normalize_percent(percent)
        return int((normalized / 100.0) * 255)
