"""Panel-local tab-group runtime coordination."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QSignalBlocker
from threep_commons.fs_paths import display_path_text

from ...explorer_tab import ExplorerTab
from ...panel_groups import (
    DEFAULT_TAB_GROUP_ID,
    DEFAULT_TAB_GROUP_TITLE,
    is_default_tab_group,
    new_tab_group_id,
    normalize_tab_group_id,
    normalize_tab_group_title,
)
from ...runtime_trace import trace_span

if TYPE_CHECKING:
    from ...panel_widget import PanelWidget
    from ..window.state_types import TabGroupState


def _tab_label(path: Path) -> str:
    """Return the tab-strip label for one filesystem path."""

    anchor = path.anchor
    if anchor and path == Path(anchor):
        return display_path_text(path)
    return path.name or display_path_text(path)


@dataclass(slots=True)
class _PanelTabGroupRuntime:
    """Track one panel-local tab group and its live tab widgets."""

    group_id: str
    title: str
    tabs: list[ExplorerTab] = field(default_factory=list)
    current_index: int = 0
    column_widths: list[int] = field(default_factory=list)


class PanelTabGroupsCoordinator:
    """Own the tab-group runtime for one panel widget."""

    def __init__(self, panel: PanelWidget) -> None:
        """Store the owning panel and initialize its default group."""

        self.panel = panel
        self._tab_groups: dict[str, _PanelTabGroupRuntime] = {}
        self._group_order: list[str] = []
        self._active_group_id = DEFAULT_TAB_GROUP_ID
        self._mounted_group_id: str | None = None
        self._ensure_default_group()

    @property
    def active_group_id(self) -> str:
        """Return the identifier of the active tab group."""

        return self._active_group_id

    @property
    def active_group_title(self) -> str:
        """Return the title of the active tab group."""

        return self._active_group().title

    def group_count(self) -> int:
        """Return the number of tab groups owned by this panel."""

        return len(self._group_order)

    def total_tab_count(self) -> int:
        """Return the total number of tabs across all panel groups."""

        return sum(len(group.tabs) for group in self._tab_groups.values())

    def ordered_group_choices(
        self,
        *,
        include_active: bool = True,
    ) -> list[tuple[str, str]]:
        """Return ordered `(group_id, title)` pairs for this panel."""

        choices: list[tuple[str, str]] = []
        for group_id in self._group_order:
            if not include_active and group_id == self._active_group_id:
                continue
            group = self._tab_groups.get(group_id)
            if group is None:
                continue
            choices.append((group.group_id, group.title))
        return choices

    def can_close_active_group(self) -> bool:
        """Return whether the active tab group can be closed."""

        return self.group_count() > 1

    def create_group(
        self,
        *,
        title: str | None = None,
        seed_paths: list[Path] | None = None,
        activate: bool = True,
    ) -> str:
        """Create a new tab group and optionally activate it."""

        group_id = new_tab_group_id()
        group_title = normalize_tab_group_title(
            title,
            fallback=self._next_group_title(),
        )
        group = _PanelTabGroupRuntime(group_id=group_id, title=group_title)
        if seed_paths is not None:
            group.tabs = [
                self.panel.build_tab_widget(Path(path)) for path in seed_paths
            ]
            if group.tabs:
                group.current_index = len(group.tabs) - 1
        self._tab_groups[group_id] = group
        self._group_order.append(group_id)
        if activate:
            self.switch_to_group(group_id, focus_view=bool(group.tabs))
        else:
            self._sync_group_picker_controls()
            self.panel.current_context_changed.emit()
            self.panel.widget_map_coordinator.sync_overlay()
        return group_id

    def rename_group(self, group_id: str, title: str) -> bool:
        """Rename one existing tab group."""

        group = self._tab_groups.get(normalize_tab_group_id(group_id))
        if group is None:
            return False
        group.title = normalize_tab_group_title(title, fallback=group.title)
        self._sync_group_picker_controls()
        self.panel.current_context_changed.emit()
        self.panel.widget_map_coordinator.sync_overlay()
        return True

    def close_group(self, group_id: str) -> bool:
        """Close one tab group when more than one group exists."""

        normalized_group_id = normalize_tab_group_id(group_id)
        if normalized_group_id not in self._tab_groups or self.group_count() <= 1:
            return False

        if normalized_group_id == self._active_group_id:
            self._save_active_group_state()
            self._remove_visible_tabs(delete_widgets=True)
        group = self._tab_groups.pop(normalized_group_id)
        self._group_order = [
            current_group_id
            for current_group_id in self._group_order
            if current_group_id != normalized_group_id
        ]
        if normalized_group_id != self._active_group_id:
            for tab in group.tabs:
                tab.deleteLater()

        if not self._group_order:
            self._active_group_id = DEFAULT_TAB_GROUP_ID
            self._ensure_default_group()
        target_group_id = (
            self._active_group_id
            if self._active_group_id in self._tab_groups
            else self._group_order[0]
        )
        self.switch_to_group(target_group_id, focus_view=True)
        return True

    def switch_to_group(self, group_id: str, *, focus_view: bool = False) -> bool:
        """Switch the visible tab strip to the requested group."""

        normalized_group_id = normalize_tab_group_id(group_id)
        if normalized_group_id not in self._tab_groups:
            return False

        current_group_id = self._mounted_group_id
        with QSignalBlocker(self.panel.tabs):
            if current_group_id in self._tab_groups:
                self._save_active_group_state()
            self._remove_visible_tabs(delete_widgets=False)
            target_group = self._tab_groups[normalized_group_id]
            for tab in target_group.tabs:
                self.panel.tabs.addTab(tab, _tab_label(tab.navigation.path))
            if target_group.tabs:
                target_index = max(
                    0,
                    min(target_group.current_index, len(target_group.tabs) - 1),
                )
                self.panel.tabs.setCurrentIndex(target_index)
                target_group.current_index = target_index
            self._active_group_id = normalized_group_id
            self._mounted_group_id = normalized_group_id

        active_group = self._active_group()
        self.panel.column_widths = list(active_group.column_widths)
        if (
            self.panel.column_widths
            and self.panel.column_width_auto_align_mode
            != self.panel.COLUMN_ALIGN_MODE_NONE
        ):
            self.panel.state_coordinator.apply_column_widths_to_panel_tabs(
                self.panel.column_widths
            )
        self._sync_group_picker_controls()
        self.panel.presentation_coordinator.sync_toolbar_for_current_tab()
        self.panel.current_context_changed.emit()
        self.panel.widget_map_coordinator.sync_overlay()
        if focus_view:
            self.panel.focus_current_view()
        return True

    def focus_relative_group(self, step: int) -> bool:
        """Move forward or backward through ordered tab groups."""

        if not self._group_order:
            return False
        if self._active_group_id in self._group_order:
            current_index = self._group_order.index(self._active_group_id)
            next_index = (current_index + step) % len(self._group_order)
        else:
            next_index = 0
        return self.switch_to_group(self._group_order[next_index], focus_view=True)

    def clone_current_tab_to_new_group(self) -> str | None:
        """Create a new group seeded with a copy of the current tab path."""

        tab = self.panel.current_tab()
        if tab is None:
            return None
        return self.create_group(seed_paths=[tab.navigation.path], activate=True)

    def move_current_tab_to_group(self, target_group_id: str) -> bool:
        """Move the current tab into another group and activate that group."""

        normalized_target_group_id = normalize_tab_group_id(target_group_id)
        if normalized_target_group_id == self._active_group_id:
            return False
        target_group = self._tab_groups.get(normalized_target_group_id)
        if target_group is None:
            return False

        current_index = self.panel.tabs.currentIndex()
        widget = self.panel.tabs.widget(current_index)
        if current_index < 0 or not isinstance(widget, ExplorerTab):
            return False

        with QSignalBlocker(self.panel.tabs):
            self.panel.tabs.removeTab(current_index)
        source_group = self._active_group()
        source_group.tabs = self._visible_tabs()
        source_group.current_index = max(self.panel.tabs.currentIndex(), 0)
        source_group.column_widths = list(self.panel.column_widths)

        target_group.tabs.append(widget)
        target_group.current_index = len(target_group.tabs) - 1

        if not source_group.tabs and self.group_count() > 1:
            self._tab_groups.pop(source_group.group_id, None)
            self._group_order = [
                group_id
                for group_id in self._group_order
                if group_id != source_group.group_id
            ]

        return self.switch_to_group(normalized_target_group_id, focus_view=True)

    def move_current_tab_to_new_group(self) -> str | None:
        """Move the current tab into a newly created tab group."""

        current_tab = self.panel.current_tab()
        if current_tab is None:
            return None
        target_group_id = self.create_group(activate=False)
        moved = self.move_current_tab_to_group(target_group_id)
        if not moved:
            self.close_group(target_group_id)
            return None
        return target_group_id

    def add_tab(self, path: Path) -> ExplorerTab:
        """Add one explorer tab to the active tab group."""

        with trace_span(
            "panel.add_tab",
            "panel",
            args={"panel_id": self.panel.panel_id},
        ):
            source_tab = self.panel.current_tab()
            source_widths = (
                list(source_tab.columns.widths) if source_tab is not None else []
            )
            tab = self.panel.build_tab_widget(path)
            self.panel.tabs.addTab(tab, _tab_label(path))
            self.panel.tabs.setCurrentWidget(tab)
            self._mounted_group_id = self._active_group_id
            self.panel.retitle_tab(tab)
            self.panel.state_coordinator.initialize_new_tab_column_widths(
                tab=tab,
                source_widths=source_widths,
            )
            self._save_active_group_state()
            self.panel.presentation_coordinator.sync_toolbar_for_current_tab()
            self.panel.activated.emit()
            self.panel.current_context_changed.emit()
            self.panel.widget_map_coordinator.sync_overlay()
            return tab

    def serialize_tab_groups(self) -> list[TabGroupState]:
        """Serialize all tab groups owned by this panel."""

        self._save_active_group_state()
        return [
            {
                "group_id": group.group_id,
                "title": group.title,
                "current_index": group.current_index,
                "tabs": [tab.serialize_state() for tab in group.tabs],
                "column_widths": list(group.column_widths),
            }
            for group in self._ordered_group_runtimes()
        ]

    def sync_active_group_state(self) -> None:
        """Persist the visible tab widget state back into the active group."""

        self._save_active_group_state()

    def restore_tab_groups(
        self,
        groups: list[TabGroupState],
        *,
        active_group_id: str,
    ) -> None:
        """Restore this panel from serialized tab-group state."""

        with trace_span(
            "panel.restore_tab_groups",
            "panel",
            args={"group_count": len(groups), "panel_id": self.panel.panel_id},
        ):
            self._clear_all_group_tabs()
            self._tab_groups = {}
            self._group_order = []

            for group_state in groups:
                group_id = normalize_tab_group_id(
                    group_state.get("group_id"),
                    fallback=new_tab_group_id(),
                )
                if group_id in self._tab_groups:
                    continue
                title = normalize_tab_group_title(
                    group_state.get("title"),
                    fallback=self._next_group_title(),
                )
                tabs = [
                    self.panel.build_tab_widget(Path(tab_state["path"]))
                    for tab_state in group_state.get("tabs", [])
                ]
                group = _PanelTabGroupRuntime(
                    group_id=group_id,
                    title=title,
                    tabs=tabs,
                    current_index=max(0, int(group_state.get("current_index", 0))),
                    column_widths=[
                        width
                        for width in group_state.get("column_widths", [])
                        if width > 0
                    ],
                )
                self._tab_groups[group_id] = group
                self._group_order.append(group_id)

            if not self._group_order:
                self._ensure_default_group()

            requested_group_id = normalize_tab_group_id(
                active_group_id,
                fallback=self._group_order[0],
            )
            target_group_id = (
                requested_group_id
                if requested_group_id in self._tab_groups
                else self._group_order[0]
            )
            self.switch_to_group(target_group_id)

    def iter_all_tabs(self) -> list[ExplorerTab]:
        """Return all explorer tabs across every tab group."""

        self._save_active_group_state()
        tabs: list[ExplorerTab] = []
        for group in self._ordered_group_runtimes():
            tabs.extend(group.tabs)
        return tabs

    def on_group_picker_index_changed(self, index: int) -> None:
        """Switch groups when the toolbar picker changes selection."""

        if index < 0:
            return
        group_id = str(self.panel.group_picker_combo.itemData(index) or "").strip()
        if not group_id:
            return
        self.switch_to_group(group_id, focus_view=True)

    def _ordered_group_runtimes(self) -> list[_PanelTabGroupRuntime]:
        """Return tab groups in their current visual order."""

        groups: list[_PanelTabGroupRuntime] = []
        for group_id in self._group_order:
            group = self._tab_groups.get(group_id)
            if group is not None:
                groups.append(group)
        return groups

    def _active_group(self) -> _PanelTabGroupRuntime:
        """Return the active tab group runtime, creating the default when needed."""

        group = self._tab_groups.get(self._active_group_id)
        if group is not None:
            return group
        self._ensure_default_group()
        active_group = self._tab_groups.get(self._active_group_id)
        if active_group is None:
            raise RuntimeError("Active tab group is missing after initialization.")
        return active_group

    def _ensure_default_group(self) -> None:
        """Ensure the panel has an implicit default tab group."""

        if self._group_order:
            self._sync_group_picker_controls()
            return
        default_group = _PanelTabGroupRuntime(
            group_id=DEFAULT_TAB_GROUP_ID,
            title=DEFAULT_TAB_GROUP_TITLE,
        )
        self._tab_groups = {DEFAULT_TAB_GROUP_ID: default_group}
        self._group_order = [DEFAULT_TAB_GROUP_ID]
        self._active_group_id = DEFAULT_TAB_GROUP_ID
        self._mounted_group_id = None
        self._sync_group_picker_controls()

    def _next_group_title(self) -> str:
        """Return the next default title for a newly created tab group."""

        existing_titles = {group.title for group in self._tab_groups.values()}
        candidate = 1
        while True:
            title = f"Group {candidate}"
            if title not in existing_titles:
                return title
            candidate += 1

    def _sync_group_picker_controls(self) -> None:
        """Refresh the toolbar group picker and its visibility."""

        with QSignalBlocker(self.panel.group_picker_combo):
            self.panel.group_picker_combo.clear()
            current_index = -1
            for index, group in enumerate(self._ordered_group_runtimes()):
                self.panel.group_picker_combo.addItem(group.title, group.group_id)
                if group.group_id == self._active_group_id:
                    current_index = index
            if current_index >= 0:
                self.panel.group_picker_combo.setCurrentIndex(current_index)
        self.panel.group_picker_combo.setVisible(self._should_show_group_picker())

    def _should_show_group_picker(self) -> bool:
        """Return whether the group picker should be shown for this panel."""

        if self.group_count() != 1:
            return True
        group = self._active_group()
        return not is_default_tab_group(group_id=group.group_id, title=group.title)

    def _visible_tabs(self) -> list[ExplorerTab]:
        """Return the explorer tabs currently mounted in the visible tab widget."""

        tabs: list[ExplorerTab] = []
        for index in range(self.panel.tabs.count()):
            widget = self.panel.tabs.widget(index)
            if isinstance(widget, ExplorerTab):
                tabs.append(widget)
        return tabs

    def _save_active_group_state(self) -> None:
        """Copy the visible tab widget state back into the active group runtime."""

        mounted_group_id = self._mounted_group_id
        if mounted_group_id is None:
            return
        group = self._tab_groups.get(mounted_group_id)
        if group is None:
            return
        group.tabs = self._visible_tabs()
        group.current_index = (
            max(self.panel.tabs.currentIndex(), 0) if group.tabs else 0
        )
        group.column_widths = list(self.panel.column_widths)

    def _remove_visible_tabs(self, *, delete_widgets: bool) -> list[ExplorerTab]:
        """Remove all visible tabs, optionally deleting their widgets."""

        tabs: list[ExplorerTab] = []
        while self.panel.tabs.count() > 0:
            widget = self.panel.tabs.widget(0)
            self.panel.tabs.removeTab(0)
            if isinstance(widget, ExplorerTab):
                tabs.append(widget)
        if delete_widgets:
            for tab in tabs:
                tab.deleteLater()
        self._mounted_group_id = None
        return tabs

    def _clear_all_group_tabs(self) -> None:
        """Delete every live tab widget tracked by this panel."""

        self._save_active_group_state()
        self._remove_visible_tabs(delete_widgets=False)
        seen_tab_ids: set[int] = set()
        for group in self._tab_groups.values():
            for tab in group.tabs:
                tab_key = id(tab)
                if tab_key in seen_tab_ids:
                    continue
                seen_tab_ids.add(tab_key)
                tab.deleteLater()
        self.panel.column_widths = []
