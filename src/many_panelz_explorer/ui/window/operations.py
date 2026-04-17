"""Window-level coordination for file, archive, and target-pane actions."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from PySide6.QtWidgets import QInputDialog, QMessageBox

from ... import file_ops, folder_sizes
from ..._operations.path_helpers import to_windows_long_path
from ..._operations.types import (
    SHORTCUT_BEHAVIOR_DIALOG,
    OperationKind,
    OperationRequest,
)
from .panels import resolve_window_target_panel_id

if TYPE_CHECKING:
    from collections.abc import Callable

    from ...explorer_tab import ExplorerTab
    from ...panel_widget import PanelWidget
    from ...window import ExplorerWindow


type ConflictChoice = Literal["overwrite", "skip", "rename", "cancel"]
type ArchiveOperationKind = Literal["pack", "unpack"]
SUPPORTED_ARCHIVE_SUFFIXES = frozenset({".7z", ".rar"})


class WindowOperationsCoordinator:
    """Coordinate file operations initiated from an explorer window."""

    def __init__(self, window: ExplorerWindow) -> None:
        """Store the owning window reference."""
        self.window = window

    def delete_selected_items(self, configure: bool = False) -> None:
        panel = self.window.panels_coordinator.active_panel()
        if panel is None:
            return
        tab = panel.current_tab()
        if tab is None:
            return
        selected = tab.marked_or_current_paths()
        if not selected:
            self.window.statusBar().showMessage(
                "No items selected in source pane.", 3000
            )
            return

        request = self.build_operation_request(
            kind="delete",
            sources=[Path(path) for path in selected],
            target_dir=None,
            configure=configure,
        )
        if request is None:
            return
        job = self.window.controller.operation_queue_manager.submit(request)
        self.window.statusBar().showMessage(
            f"Delete job {job.job_id[:8]}: {job.status}.",
            3500,
        )
        if job.status in {"succeeded", "failed", "cancelled"}:
            panel.navigation_coordinator.refresh_current_path()

    def pack_sources(self, *, sources: list[Path]) -> None:
        """Open the archive pack dialog for the provided source items."""

        if not sources:
            self.window.statusBar().showMessage(
                "No items selected in source pane.",
                3000,
            )
            return

        source_tab = self._active_source_tab()
        self._maybe_queue_directory_sizes(
            source_tab=source_tab,
            sources=sources,
            enabled=self.window.settings.auto_calculate_dir_sizes_before_archive,
        )
        request = self.build_archive_request(
            kind="pack",
            sources=sources,
            source_tab=source_tab,
        )
        if request is None:
            return
        job = self.window.controller.operation_queue_manager.submit(request)
        self.window.statusBar().showMessage(
            f"Pack job {job.job_id[:8]}: {job.status}.",
            3500,
        )
        panel = self.window.panels_coordinator.active_panel()
        if panel is not None and job.status in {"succeeded", "failed", "cancelled"}:
            panel.navigation_coordinator.refresh_current_path()

    def pack_selected_sources_in_tab(self, tab: ExplorerTab) -> None:
        """Pack the current tab selection through the shared archive workflow."""

        self.pack_sources(sources=self._selected_or_current_paths(tab))

    def unpack_archive(self, *, archive: Path) -> None:
        """Open the archive unpack dialog for the provided archive path."""

        source_tab = self._active_source_tab()
        self._maybe_queue_directory_sizes(
            source_tab=source_tab,
            sources=[Path(archive)],
            enabled=self.window.settings.auto_calculate_dir_sizes_before_archive,
        )
        request = self.build_archive_request(
            kind="unpack",
            sources=[Path(archive)],
            source_tab=source_tab,
        )
        if request is None:
            return
        job = self.window.controller.operation_queue_manager.submit(request)
        self.window.statusBar().showMessage(
            f"Unpack job {job.job_id[:8]}: {job.status}.",
            3500,
        )
        panel = self.window.panels_coordinator.active_panel()
        if panel is not None and job.status in {"succeeded", "failed", "cancelled"}:
            panel.navigation_coordinator.refresh_current_path()

    def unpack_selected_archive_in_tab(self, tab: ExplorerTab) -> None:
        """Unpack one selected archive from the provided explorer tab."""

        archive = self._single_selected_or_current_path(tab)
        if archive is None or not archive.is_file():
            return
        if archive.suffix.casefold() not in SUPPORTED_ARCHIVE_SUFFIXES:
            self.window.statusBar().showMessage(
                "Alt+F9 supports only .7z and .rar archives.",
                2400,
            )
            return
        self.unpack_archive(archive=archive)

    def test_archives(self, *, archives: list[Path]) -> None:
        """Queue or run an archive-integrity test for supported selections."""

        supported = [
            Path(path)
            for path in archives
            if Path(path).is_file()
            and Path(path).suffix.casefold() in SUPPORTED_ARCHIVE_SUFFIXES
        ]
        if not supported:
            self.window.statusBar().showMessage(
                "Alt+Shift+F9 supports only .7z and .rar archives.",
                3000,
            )
            return

        preferences = self.window.settings.ui_preferences()
        request = OperationRequest(
            kind="archive_test",
            sources=tuple(supported),
            target_dir=None,
            backend_id=preferences.default_archive_unpacker_backend,
            dispatch_mode=preferences.default_operation_dispatch_mode,
            conflict_policy=preferences.default_operation_conflict_policy,
            created_by=f"window:{self.window.window_id}",
        )
        job = self.window.controller.operation_queue_manager.submit(request)
        self.window.statusBar().showMessage(
            f"Archive test job {job.job_id[:8]}: {job.status}.",
            3500,
        )

    def test_selected_archives_in_tab(self, tab: ExplorerTab) -> None:
        """Test the current tab archive selection through the shared workflow."""

        selected_archives = [
            path
            for path in self._selected_or_current_paths(tab)
            if path.is_file() and path.suffix.casefold() in SUPPORTED_ARCHIVE_SUFFIXES
        ]
        self.test_archives(archives=selected_archives)

    def transfer_selected_to_target(
        self, *, move: bool, configure: bool = False
    ) -> None:
        source_panel = self.window.panels_coordinator.active_panel()
        source_id = self.window.active_panel_id
        if source_panel is None or source_id is None:
            return
        source_tab = source_panel.current_tab()
        if source_tab is None:
            return

        selected = source_tab.marked_or_current_paths()
        if not selected:
            self.window.statusBar().showMessage(
                "No items selected in source pane.", 3000
            )
            return

        target_id = resolve_window_target_panel_id(self.window, source_id)
        if target_id is None:
            QMessageBox.information(
                self.window,
                "Target Pane",
                "No target pane is available. Create another pane first.",
            )
            return
        target_panel = self.window.panel_widgets.get(target_id)
        if target_panel is None:
            return
        destination = target_panel.current_path()

        kind = "move" if move else "copy"
        self._maybe_queue_directory_sizes(
            source_tab=source_tab,
            sources=selected,
            enabled=self.window.settings.auto_calculate_dir_sizes_before_copy_move,
        )
        request = self.build_operation_request(
            kind=kind,
            sources=[Path(path) for path in selected],
            target_dir=destination,
            configure=configure,
            source_tab=source_tab,
        )
        if request is None:
            return
        job = self.window.controller.operation_queue_manager.submit(request)
        verb = "Move" if move else "Copy"
        self.window.statusBar().showMessage(
            f"{verb} job {job.job_id[:8]}: {job.status}.",
            3500,
        )
        if job.status in {"succeeded", "failed", "cancelled"}:
            source_panel.navigation_coordinator.refresh_current_path()
            target_panel.navigation_coordinator.refresh_current_path()

    def calculate_selected_or_current_folder_sizes_in_tab(
        self,
        tab: ExplorerTab,
    ) -> None:
        """Calculate sizes for selected folders or the current folder row."""

        targets = [
            path for path in self._selected_or_current_paths(tab) if path.is_dir()
        ]
        if not targets:
            self.window.statusBar().showMessage(
                "Select one folder, or place the cursor on a folder, first.",
                2600,
            )
            return
        self.queue_folder_size_calculation(tab=tab, paths=targets, announce=True)

    def calculate_visible_folder_sizes_in_tab(self, tab: ExplorerTab) -> None:
        """Calculate sizes for every visible folder in the active file list."""

        targets = tab.model.visible_directory_paths()
        if not targets:
            self.window.statusBar().showMessage(
                "No visible folders are available for size calculation.",
                2600,
            )
            return
        self.queue_folder_size_calculation(tab=tab, paths=targets, announce=True)

    def queue_folder_size_calculation(
        self,
        *,
        tab: ExplorerTab,
        paths: list[Path],
        announce: bool,
    ) -> int:
        """Queue one folder-size batch using the configured preferred backend."""

        calculator = folder_sizes.build_folder_size_calculator(
            use_everything_sdk=self.window.settings.use_everything_sdk_for_folder_sizes,
            everything_executable=self.window.settings.everything_executable,
        )
        queued = tab.model.request_folder_sizes(paths, calculator=calculator)
        if not announce:
            return int(queued)
        if queued <= 0:
            self.window.statusBar().showMessage(
                "Folder sizes are already calculated or in progress.",
                2400,
            )
            return int(queued)
        if calculator.uses_everything_sdk:
            self.window.statusBar().showMessage(
                "Calculating folder sizes with Everything SDK when available.",
                2600,
            )
            return int(queued)
        self.window.statusBar().showMessage(
            "Calculating folder sizes with native recursive scanning.",
            2600,
        )
        return int(queued)

    def create_directory_in_target_for_tab(self, tab: ExplorerTab) -> None:
        """Create one folder in the resolved target pane for the active tab."""

        target_panel = self._target_panel_for_tab(tab)
        if target_panel is None:
            self.window.statusBar().showMessage(
                "No target pane is available. Create another pane first.",
                2400,
            )
            return
        suggested_name = "New Folder"
        selected = self._single_selected_or_current_path(tab)
        if selected is not None:
            suggested_name = selected.name or suggested_name
        name, ok = QInputDialog.getText(
            self.window,
            "New folder in target pane",
            "Folder name:",
            text=suggested_name,
        )
        if not ok or not name.strip():
            return

        created_path: Path | None = None

        def _create() -> None:
            nonlocal created_path
            created_path = file_ops.create_folder(
                target_panel.current_path(),
                name.strip(),
            )

        if not self._run_action(_create):
            return
        target_tab = target_panel.current_tab()
        if target_tab is not None and created_path is not None:
            target_tab.navigation.set_path(
                target_panel.current_path(),
                push_history=False,
                selection_hint=created_path,
            )
        target_panel.navigation_coordinator.refresh_current_path()

    def open_selected_or_current_in_target_pane(self, tab: ExplorerTab) -> None:
        """Mirror one selected folder, or the current path, into the target pane."""

        target_panel = self._target_panel_for_tab(tab)
        if target_panel is None:
            self.window.statusBar().showMessage(
                "No target pane is available. Create another pane first.",
                2400,
            )
            return
        candidate = self._single_selected_or_current_path(tab)
        target_path = (
            candidate
            if candidate is not None and candidate.is_dir()
            else tab.navigation.path
        )
        target_tab = target_panel.current_tab()
        if target_tab is None:
            return
        target_tab.navigation.set_path(target_path)

    def build_operation_request(
        self,
        *,
        kind: OperationKind,
        sources: list[Path],
        target_dir: Path | None,
        configure: bool,
        source_tab: ExplorerTab | None = None,
    ) -> OperationRequest | None:
        ui_preferences = self.window.settings.ui_preferences()
        use_dialog = bool(configure) or (
            self.window.preferences_coordinator.operation_shortcut_behavior
            == SHORTCUT_BEHAVIOR_DIALOG
        )
        if use_dialog:
            from ...dialogs.operation_dialog import OperationDialog

            dialog = OperationDialog(
                kind=kind,
                sources=sources,
                target_dir=target_dir,
                preferences=ui_preferences,
                source_model=(source_tab.model if source_tab is not None else None),
                parent=self.window,
            )
            if dialog.exec() != dialog.DialogCode.Accepted:
                return None
            return dialog.build_request(
                kind=kind,
                sources=sources,
                target_dir=target_dir,
                created_by=f"window:{self.window.window_id}",
            )

        backend_id = (
            self.window.preferences_coordinator.default_delete_backend
            if kind == "delete"
            else self.window.preferences_coordinator.default_copy_move_backend
        )
        return OperationRequest(
            kind=kind,
            sources=tuple(sources),
            target_dir=target_dir,
            backend_id=backend_id,
            dispatch_mode=(
                self.window.preferences_coordinator.default_operation_dispatch_mode
            ),
            conflict_policy=(
                self.window.preferences_coordinator.default_operation_conflict_policy
            ),
            created_by=f"window:{self.window.window_id}",
        )

    def build_archive_request(
        self,
        *,
        kind: ArchiveOperationKind,
        sources: list[Path],
        source_tab: ExplorerTab | None = None,
    ) -> OperationRequest | None:
        """Open the archive dialog and build a request from it."""

        from ...dialogs.archive_operation_dialog import ArchiveOperationDialog

        dialog = ArchiveOperationDialog(
            kind=kind,
            sources=sources,
            preferences=self.window.settings.ui_preferences(),
            source_model=(source_tab.model if source_tab is not None else None),
            parent=self.window,
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return None
        return dialog.build_request(created_by=f"window:{self.window.window_id}")

    def copy_or_move_one(
        self, *, source: Path, destination_dir: Path, move: bool
    ) -> Literal["done", "skip", "cancel"]:
        destination_dir = Path(destination_dir)
        destination = destination_dir / source.name
        if destination.exists():
            choice = self.prompt_conflict_resolution(source, destination)
            if choice == "cancel":
                return "cancel"
            if choice == "skip":
                return "skip"
            if choice == "rename":
                destination = self.next_available_path(destination_dir, source.name)
            elif choice == "overwrite":
                if source.resolve() == destination.resolve():
                    return "skip"
                self.remove_existing_path(destination)
        try:
            source_raw = to_windows_long_path(source)
            destination_raw = to_windows_long_path(destination)
            if move:
                shutil.move(source_raw, destination_raw)
            else:
                if source.is_dir():
                    shutil.copytree(source_raw, destination_raw)
                else:
                    shutil.copy2(source_raw, destination_raw)
        except Exception as exc:  # pragma: no cover - UI error path
            QMessageBox.critical(self.window, "File Operation Failed", str(exc))
            return "cancel"
        return "done"

    def prompt_conflict_resolution(
        self, source: Path, destination: Path
    ) -> ConflictChoice:
        dialog = QMessageBox(self.window)
        dialog.setWindowTitle("Name Conflict")
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setText(
            f'"{destination.name}" already exists in target pane.\n\n'
            f"Source: {source}\nTarget: {destination}"
        )
        overwrite_button = dialog.addButton(
            "Overwrite", QMessageBox.ButtonRole.AcceptRole
        )
        skip_button = dialog.addButton("Skip", QMessageBox.ButtonRole.ActionRole)
        rename_button = dialog.addButton("Rename", QMessageBox.ButtonRole.ActionRole)
        cancel_button = dialog.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        dialog.exec()
        clicked = dialog.clickedButton()
        if clicked is overwrite_button:
            return "overwrite"
        if clicked is skip_button:
            return "skip"
        if clicked is rename_button:
            return "rename"
        _ = cancel_button
        return "cancel"

    def next_available_path(self, destination_dir: Path, base_name: str) -> Path:
        candidate = destination_dir / base_name
        if not candidate.exists():
            return candidate
        stem = candidate.stem
        suffix = candidate.suffix
        counter = 1
        while True:
            candidate = destination_dir / f"{stem} ({counter}){suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    def remove_existing_path(self, path: Path) -> None:
        raw = to_windows_long_path(path)
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(raw)
            return
        Path(raw).unlink()

    def _active_source_tab(self) -> ExplorerTab | None:
        """Return the active source tab for copy, move, and archive actions."""

        panel = self.window.panels_coordinator.active_panel()
        if panel is None:
            return None
        return panel.current_tab()

    def _maybe_queue_directory_sizes(
        self,
        *,
        source_tab: ExplorerTab | None,
        sources: list[Path],
        enabled: bool,
    ) -> None:
        """Queue size calculations for selected directories when enabled."""

        if not enabled or source_tab is None:
            return
        directories = [Path(path) for path in sources if Path(path).is_dir()]
        if not directories:
            return
        self.queue_folder_size_calculation(
            tab=source_tab,
            paths=directories,
            announce=False,
        )

    def _selected_or_current_paths(self, tab: ExplorerTab) -> list[Path]:
        """Return selected paths, or fall back to the current row for one tab."""

        selected = tab.selected_paths()
        if selected:
            return selected
        current = tab.current_path_or_none()
        return [current] if current is not None else []

    def _single_selected_or_current_path(self, tab: ExplorerTab) -> Path | None:
        """Return one selected or current path when the tab resolves exactly one."""

        paths = self._selected_or_current_paths(tab)
        if len(paths) != 1:
            return None
        return paths[0]

    def _target_panel_for_tab(self, tab: ExplorerTab) -> PanelWidget | None:
        """Resolve the current target panel when the provided tab is active."""

        active_panel = self.window.panels_coordinator.active_panel()
        if active_panel is None or active_panel.current_tab() is not tab:
            return None
        target_panel = self.window.panels_coordinator.target_panel()
        if target_panel is active_panel:
            return None
        return target_panel

    def _run_action(self, action: Callable[[], object]) -> bool:
        """Run one local action and surface UI failures consistently."""

        try:
            action()
        except Exception as exc:  # pragma: no cover - UI error path
            QMessageBox.critical(self.window, "Operation failed", str(exc))
            return False
        return True
