"""Persistence helpers for saving and restoring window state."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtWidgets import QMessageBox

from ...panel_tree import PanelTreeModel
from ...runtime_trace import trace_span
from ...window_state_payloads import (
    coerce_bool as _coerce_bool,
)
from ...window_state_payloads import (
    panel_tree_payload as _panel_tree_payload,
)
from ...window_state_payloads import (
    saved_view_state as _saved_view_state,
)
from ...window_state_payloads import (
    tabs_state_from_panels_payload as _tabs_state_from_panels_payload,
)
from ...window_state_payloads import (
    window_tabs_payload as _window_tabs_payload,
)
from .panels import serialize_window_tabs_state

if TYPE_CHECKING:
    from ...window import ExplorerWindow
    from .state_types import (
        SavedViewState,
        WindowStatePayload,
        WindowStateSnapshot,
        WindowTabsPayload,
    )


class WindowPersistenceCoordinator:
    """Serialize and restore panel, tab, and geometry state for a window."""

    def __init__(self, window: ExplorerWindow) -> None:
        self.window = window

    def encode_geometry(self) -> str:
        geometry = self.window.saveGeometry()
        encoded = geometry.toBase64().data()
        return bytes(encoded).decode("ascii")

    def restore_geometry_from_b64(self, encoded: str) -> None:
        raw = QByteArray.fromBase64(encoded.encode("ascii"))
        if not raw.isEmpty():
            self.window.default_maximize_on_first_show = False
            self.window.restoreGeometry(raw)

    def capture_snapshot(
        self,
        *,
        include_geometry: bool = False,
    ) -> WindowStateSnapshot:
        """Capture the current live window into the shared snapshot contract."""

        self.window.layout_coordinator.sync_panel_tree_from_rows()
        snapshot: WindowStatePayload = {
            "window_id": self.window.window_id,
            "panel_tree": self.window.panel_tree.to_dict(),
            "tabs": serialize_window_tabs_state(self.window),
            "active_panel_id": self.window.active_panel_id,
            "recently_closed_tabs": deepcopy(self.window.recently_closed_tabs),
            "on_top": self.window.on_top_action.isChecked(),
            "maximized": self._is_window_maximized(),
        }
        if include_geometry:
            snapshot["geometry_b64"] = self.encode_geometry()
        return snapshot

    def serialize_state(
        self,
        *,
        include_geometry: bool = False,
    ) -> WindowStateSnapshot:
        """Return a snapshot using the legacy persistence API name."""

        return self.capture_snapshot(include_geometry=include_geometry)

    def saved_view_names(self) -> list[str]:
        """Return saved view names in stable display order."""

        return self.window.settings.list_saved_views()

    def saved_view_snapshot(self, view_name: str) -> SavedViewState | None:
        """Return one normalized saved-view snapshot when it exists."""

        return self.window.settings.get_saved_view(view_name)

    def save_named_view(self, view_name: str) -> WindowStateSnapshot:
        """Persist the current snapshot as one named saved view."""

        snapshot = self.capture_snapshot(include_geometry=True)
        self.window.settings.set_saved_view(view_name, snapshot)
        self.window.settings.sync()
        return snapshot

    def clone_to_new_window(self) -> ExplorerWindow:
        """Open a new window from the current live snapshot."""

        return self.open_snapshot_in_new_window(
            self.capture_snapshot(),
            restore_geometry=False,
        )

    def open_saved_view_in_new_window(self, view_name: str) -> ExplorerWindow | None:
        """Open one saved view in a new window when it exists."""

        snapshot = self.saved_view_snapshot(view_name)
        if snapshot is None:
            return None
        return self.open_snapshot_in_new_window(snapshot, restore_geometry=True)

    def replace_from_saved_view(self, view_name: str) -> bool:
        """Replace the current window from one saved view when present."""

        snapshot = self.saved_view_snapshot(view_name)
        if snapshot is None:
            return False
        self.apply_snapshot(snapshot, restore_geometry=True)
        return True

    def open_snapshot_in_new_window(
        self,
        snapshot: WindowStateSnapshot,
        *,
        restore_geometry: bool,
    ) -> ExplorerWindow:
        """Create a new window and hydrate it from one shared snapshot."""

        new_window = self.window.controller.new_window(
            from_window=self.window,
            show=False,
        )
        new_window.persistence_coordinator.apply_snapshot(
            snapshot,
            restore_geometry=restore_geometry,
        )
        new_window.show()
        return new_window

    def save_to_settings(self) -> None:
        """Persist the current session-backed window state into settings."""

        with trace_span("window_state.save_to_settings", "persistence"):
            snapshot = self.capture_snapshot()
            self.window.settings.set_json(
                self.window.settings.window_key(self.window.window_id, "panel_tree"),
                snapshot["panel_tree"],
            )

            tabs_payload: WindowTabsPayload = {
                "active_panel_id": snapshot["active_panel_id"],
                "panels": {str(pid): state for pid, state in snapshot["tabs"].items()},
                "recently_closed_tabs": snapshot["recently_closed_tabs"],
            }
            self.window.settings.set_json(
                self.window.settings.window_key(self.window.window_id, "tabs"),
                tabs_payload,
            )
            self.window.settings.set_value(
                self.window.settings.window_key(self.window.window_id, "on_top"),
                snapshot["on_top"],
            )
            self.window.settings.set_value(
                self.window.settings.window_key(self.window.window_id, "geometry"),
                self.window.saveGeometry(),
            )
            self.window.settings.set_value(
                self.window.settings.window_key(self.window.window_id, "maximized"),
                self._is_window_maximized(),
            )

    def restore_from_settings(self) -> None:
        """Restore panel layout, tabs, and geometry state from settings."""

        with trace_span("window_state.restore_from_settings", "persistence"):
            panel_tree_data = self.window.settings.get_json(
                self.window.settings.window_key(self.window.window_id, "panel_tree"),
                None,
            )
            panel_tree_payload = _panel_tree_payload(panel_tree_data)
            panel_tree_model = self.window.layout_coordinator.default_startup_tree()
            if panel_tree_payload is not None:
                try:
                    panel_tree_model = PanelTreeModel.from_dict(panel_tree_payload)
                except Exception as exc:  # pragma: no cover - defensive path
                    QMessageBox.warning(
                        self.window, "Restore", f"Could not restore panel tree: {exc}"
                    )

            tabs_payload_raw = self.window.settings.get_json(
                self.window.settings.window_key(self.window.window_id, "tabs"), {}
            )
            tabs_payload = _window_tabs_payload(tabs_payload_raw)
            on_top_value = self.window.settings.value(
                self.window.settings.window_key(self.window.window_id, "on_top"), False
            )
            geometry = self.window.settings.value(
                self.window.settings.window_key(self.window.window_id, "geometry")
            )
            maximized_value = self.window.settings.value(
                self.window.settings.window_key(self.window.window_id, "maximized"),
                False,
            )
            maximized = _coerce_bool(maximized_value)
            snapshot: WindowStateSnapshot = {
                "window_id": self.window.window_id,
                "panel_tree": panel_tree_model.to_dict(),
                "tabs": _tabs_state_from_panels_payload(tabs_payload["panels"]),
                "active_panel_id": tabs_payload["active_panel_id"],
                "recently_closed_tabs": deepcopy(tabs_payload["recently_closed_tabs"]),
                "on_top": _coerce_bool(on_top_value),
                "maximized": maximized,
            }
            if isinstance(geometry, QByteArray) and not geometry.isEmpty():
                encoded_geometry = geometry.toBase64().data()
                snapshot["geometry_b64"] = bytes(encoded_geometry).decode("ascii")

            self._restore_snapshot_contents(
                snapshot,
                panel_tree_model=panel_tree_model,
            )

            if isinstance(geometry, QByteArray) or maximized:
                self.window.default_maximize_on_first_show = False
                geometry_b64 = snapshot.get("geometry_b64")
                if isinstance(geometry_b64, str) and geometry_b64:
                    self.restore_geometry_from_b64(geometry_b64)
                self._apply_maximized_state(maximized)

    def apply_snapshot(
        self,
        snapshot: WindowStateSnapshot,
        *,
        restore_geometry: bool = False,
    ) -> None:
        """Apply one normalized snapshot to the current live window."""

        with trace_span(
            "window_state.apply_snapshot",
            "persistence",
            args={"restore_geometry": restore_geometry},
        ):
            self.window.default_maximize_on_first_show = False
            payload = _saved_view_state(snapshot)
            self._restore_snapshot_contents(payload)
            if restore_geometry:
                geometry_b64 = payload.get("geometry_b64")
                if isinstance(geometry_b64, str) and geometry_b64:
                    self.restore_geometry_from_b64(geometry_b64)
                self._apply_maximized_state(payload["maximized"])

    def apply_cloned_state(
        self,
        state: SavedViewState,
        *,
        restore_geometry: bool = False,
    ) -> None:
        """Apply a snapshot using the legacy clone-window API name."""

        self.apply_snapshot(state, restore_geometry=restore_geometry)

    def _restore_snapshot_contents(
        self,
        snapshot: WindowStateSnapshot,
        *,
        panel_tree_model: PanelTreeModel | None = None,
    ) -> None:
        """Restore layout, tabs, and on-top state from one snapshot."""

        payload = _saved_view_state(snapshot)
        restored_panel_tree = (
            panel_tree_model
            if panel_tree_model is not None
            else PanelTreeModel.from_dict(payload["panel_tree"])
        )
        tabs_state = deepcopy(payload["tabs"])
        self.window.panel_tree = restored_panel_tree
        self.window.layout_rows = self.window.layout_coordinator.rows_from_tree(
            self.window.panel_tree.root
        )
        self.window.recently_closed_tabs = deepcopy(payload["recently_closed_tabs"])
        self.window.layout_rows = (
            self.window.layout_coordinator.append_missing_panel_ids(
                self.window.layout_rows,
                list(tabs_state.keys()),
            )
        )
        self.window.layout_coordinator.sync_panel_tree_from_rows()
        self.window.panels_coordinator.rebuild_from_tree(
            tabs_state=tabs_state,
            preferred_active_panel=payload["active_panel_id"],
        )
        self.window.set_on_top(payload["on_top"])

    def _apply_maximized_state(self, maximized: bool) -> None:
        """Apply the persisted maximized state to the window."""
        if maximized:
            self.window.setWindowState(
                self.window.windowState() | Qt.WindowState.WindowMaximized
            )
            return
        self.window.setWindowState(
            self.window.windowState() & ~Qt.WindowState.WindowMaximized
        )

    def _is_window_maximized(self) -> bool:
        """Return whether the window state currently includes maximize."""

        return bool(self.window.windowState() & Qt.WindowState.WindowMaximized)
