"""Archive pack and unpack configuration dialogs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .._operations.types import (
    BACKEND_ARCHIVE_7ZIP,
    BACKEND_ARCHIVE_WINRAR,
    DISPATCH_MODE_QUEUE,
    OperationRequest,
)
from ..selection_size_summary import (
    build_selection_size_line,
    build_selection_size_snapshot,
)

if TYPE_CHECKING:
    from .._settings.models import UiPreferences
    from ..fast_dir_model import FastDirModel


type ArchiveOperationKind = Literal["pack", "unpack"]


@dataclass(frozen=True)
class ArchiveDialogResult:
    """Capture the user's archive-dialog configuration."""

    backend_id: str
    dispatch_mode: str
    target_dir: Path | None
    target_path: Path | None
    backend_options: dict[str, str]


class ArchiveOperationDialog(QDialog):
    """Collect pack or unpack settings for one archive operation."""

    def __init__(
        self,
        *,
        kind: ArchiveOperationKind,
        sources: list[Path],
        preferences: UiPreferences,
        source_model: FastDirModel | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._kind: ArchiveOperationKind = kind
        self._sources = [Path(source) for source in sources]
        self._preferences = preferences
        self._source_model = source_model

        self.setModal(True)
        self.resize(700, 520)
        self.setWindowTitle("Pack Files" if self._kind == "pack" else "Unpack Files")

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        self.summary_label = QLabel(self._summary_text(), self)
        self.summary_label.setWordWrap(True)
        self.summary_label.setTextFormat(Qt.TextFormat.PlainText)
        root.addWidget(self.summary_label)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(8)

        self.backend_combo = QComboBox(self)
        self.backend_combo.addItem("WinRAR", BACKEND_ARCHIVE_WINRAR)
        self.backend_combo.addItem("7-Zip", BACKEND_ARCHIVE_7ZIP)
        self._set_combo_data(
            self.backend_combo,
            (
                preferences.default_archive_packer_backend
                if self._kind == "pack"
                else preferences.default_archive_unpacker_backend
            ),
        )
        self.backend_combo.currentIndexChanged.connect(self._sync_backend_state)
        form.addRow("Backend", self.backend_combo)

        self.dispatch_combo = QComboBox(self)
        self.dispatch_combo.addItem("Queue", "queue")
        self.dispatch_combo.addItem("Launch Now (No Wait)", "launch_now_no_wait")
        self.dispatch_combo.addItem("Run Now (Wait)", "run_now_wait")
        self._set_combo_data(
            self.dispatch_combo,
            preferences.default_operation_dispatch_mode or DISPATCH_MODE_QUEUE,
        )
        form.addRow("Dispatch", self.dispatch_combo)

        self.target_edit = QLineEdit(self)
        self.target_browse_btn = QPushButton("Browse...", self)
        self.target_browse_btn.clicked.connect(self._browse_target)
        target_row = QWidget(self)
        target_layout = QHBoxLayout(target_row)
        target_layout.setContentsMargins(0, 0, 0, 0)
        target_layout.setSpacing(8)
        target_layout.addWidget(self.target_edit, 1)
        target_layout.addWidget(self.target_browse_btn)
        form.addRow(
            "Archive file" if self._kind == "pack" else "Destination",
            target_row,
        )

        root.addLayout(form)

        self.options_scroll = QScrollArea(self)
        self.options_scroll.setWidgetResizable(True)
        self.options_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.options_host = QWidget(self.options_scroll)
        self.options_layout = QVBoxLayout(self.options_host)
        self.options_layout.setContentsMargins(0, 0, 0, 0)
        self.options_layout.setSpacing(8)

        self.common_pack_group = self._build_common_pack_group()
        self.common_unpack_group = self._build_common_unpack_group()
        self.winrar_pack_group = self._build_winrar_pack_group()
        self.seven_zip_pack_group = self._build_seven_zip_pack_group()
        self.winrar_unpack_group = self._build_winrar_unpack_group()
        self.seven_zip_unpack_group = self._build_seven_zip_unpack_group()

        self.options_layout.addWidget(self.common_pack_group)
        self.options_layout.addWidget(self.common_unpack_group)
        self.options_layout.addWidget(self.winrar_pack_group)
        self.options_layout.addWidget(self.seven_zip_pack_group)
        self.options_layout.addWidget(self.winrar_unpack_group)
        self.options_layout.addWidget(self.seven_zip_unpack_group)
        self.options_layout.addStretch(1)
        self.options_scroll.setWidget(self.options_host)
        root.addWidget(self.options_scroll, 1)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)

        if self._kind == "pack":
            self.target_edit.setText(str(self._suggest_pack_target_path()))
        else:
            self.target_edit.setText(str(self._suggest_unpack_target_dir()))
        self._sync_backend_state()
        self._sync_password_state()
        if self._source_model is not None:
            self._source_model.folder_size_state_changed.connect(
                self._refresh_summary_text
            )

    def _summary_text(self) -> str:
        lines = [f"Operation: {self._kind.title()}"]
        lines.append(f"Items: {len(self._sources)}")
        lines.append(self._selection_size_line())
        lines.extend(str(source) for source in self._sources[:5])
        if len(self._sources) > 5:
            lines.append(f"... +{len(self._sources) - 5} more")
        return "\n".join(lines)

    def _selection_size_line(self) -> str:
        """Render the current known source-selection size summary."""

        snapshot = build_selection_size_snapshot(
            sources=self._sources,
            model=self._source_model,
        )
        if self._source_model is not None:
            size_formatter = self._source_model.format_size_value
        else:
            size_formatter = self._default_size_formatter
        return build_selection_size_line(snapshot, size_formatter=size_formatter)

    def _refresh_summary_text(self, *_args: object) -> None:
        """Refresh the summary label after background size updates."""

        self.summary_label.setText(self._summary_text())

    def _default_size_formatter(self, value: int) -> str:
        """Format bytes for summary-only dialogs without a live model."""

        return f"{int(value):,}"

    def _build_winrar_pack_group(self) -> QWidget:
        group = QWidget(self.options_host)
        layout = QGridLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)

        self.winrar_pack_level_combo = QComboBox(group)
        self.winrar_pack_level_combo.addItem("Store", "-m0")
        self.winrar_pack_level_combo.addItem("Fastest", "-m1")
        self.winrar_pack_level_combo.addItem("Fast", "-m2")
        self.winrar_pack_level_combo.addItem("Normal", "-m3")
        self.winrar_pack_level_combo.addItem("Good", "-m4")
        self.winrar_pack_level_combo.addItem("Best", "-m5")
        self.winrar_pack_level_combo.setCurrentIndex(3)
        self.winrar_pack_recurse_checkbox = QCheckBox("Recurse subfolders (-r)", group)
        self.winrar_pack_recurse_checkbox.setChecked(True)
        self.winrar_pack_solid_checkbox = QCheckBox("Solid archive (-s)", group)
        self.winrar_pack_solid_checkbox.setChecked(True)
        self.winrar_pack_recovery_checkbox = QCheckBox(
            "Recovery record (-rr3p)",
            group,
        )
        self.winrar_pack_lock_checkbox = QCheckBox("Lock archive (-k)", group)
        self.winrar_pack_extra_args_edit = QLineEdit(group)
        self.winrar_pack_extra_args_edit.setPlaceholderText(
            "Additional WinRAR pack args"
        )

        layout.addWidget(QLabel("Compression", group), 0, 0)
        layout.addWidget(self.winrar_pack_level_combo, 0, 1)
        layout.addWidget(self.winrar_pack_recurse_checkbox, 1, 0, 1, 2)
        layout.addWidget(self.winrar_pack_solid_checkbox, 2, 0, 1, 2)
        layout.addWidget(self.winrar_pack_recovery_checkbox, 3, 0, 1, 2)
        layout.addWidget(self.winrar_pack_lock_checkbox, 4, 0, 1, 2)
        layout.addWidget(QLabel("Extra args", group), 5, 0)
        layout.addWidget(self.winrar_pack_extra_args_edit, 5, 1)
        layout.setColumnStretch(1, 1)
        return group

    def _build_common_pack_group(self) -> QWidget:
        group = QWidget(self.options_host)
        layout = QGridLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)

        self.pack_password_edit = QLineEdit(group)
        self.pack_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pack_password_edit.setPlaceholderText("Optional archive password")
        self.pack_password_edit.textChanged.connect(self._sync_password_state)
        self.pack_encrypt_names_checkbox = QCheckBox(
            "Encrypt file names when supported",
            group,
        )
        self.pack_split_size_edit = QLineEdit(group)
        self.pack_split_size_edit.setPlaceholderText("Optional split size, e.g. 100m")
        self.pack_sfx_checkbox = QCheckBox("Create self-extracting archive", group)
        self.pack_test_checkbox = QCheckBox("Test archive after creation", group)

        layout.addWidget(QLabel("Password", group), 0, 0)
        layout.addWidget(self.pack_password_edit, 0, 1)
        layout.addWidget(self.pack_encrypt_names_checkbox, 1, 0, 1, 2)
        layout.addWidget(QLabel("Split volume", group), 2, 0)
        layout.addWidget(self.pack_split_size_edit, 2, 1)
        layout.addWidget(self.pack_sfx_checkbox, 3, 0, 1, 2)
        layout.addWidget(self.pack_test_checkbox, 4, 0, 1, 2)
        layout.setColumnStretch(1, 1)
        return group

    def _build_seven_zip_pack_group(self) -> QWidget:
        group = QWidget(self.options_host)
        layout = QGridLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)

        self.seven_zip_pack_recurse_checkbox = QCheckBox(
            "Recurse subfolders (-r)",
            group,
        )
        self.seven_zip_pack_recurse_checkbox.setChecked(True)
        self.seven_zip_pack_level_combo = QComboBox(group)
        self.seven_zip_pack_level_combo.addItem("Store", "-mx=0")
        self.seven_zip_pack_level_combo.addItem("Fastest", "-mx=1")
        self.seven_zip_pack_level_combo.addItem("Fast", "-mx=3")
        self.seven_zip_pack_level_combo.addItem("Normal", "-mx=5")
        self.seven_zip_pack_level_combo.addItem("Maximum", "-mx=7")
        self.seven_zip_pack_level_combo.addItem("Ultra", "-mx=9")
        self.seven_zip_pack_level_combo.setCurrentIndex(3)
        self.seven_zip_pack_method_combo = QComboBox(group)
        self.seven_zip_pack_method_combo.addItem("LZMA2", "-m0=LZMA2")
        self.seven_zip_pack_method_combo.addItem("LZMA", "-m0=LZMA")
        self.seven_zip_pack_method_combo.addItem("PPMd", "-m0=PPMd")
        self.seven_zip_pack_method_combo.addItem("Copy", "-m0=Copy")
        self.seven_zip_pack_solid_checkbox = QCheckBox(
            "Solid archive (-ms=on)",
            group,
        )
        self.seven_zip_pack_solid_checkbox.setChecked(True)
        self.seven_zip_pack_header_checkbox = QCheckBox(
            "Header compression (-mhc=on)",
            group,
        )
        self.seven_zip_pack_header_checkbox.setChecked(True)
        self.seven_zip_pack_extra_args_edit = QLineEdit(group)
        self.seven_zip_pack_extra_args_edit.setPlaceholderText(
            "Additional 7-Zip pack args"
        )

        layout.addWidget(self.seven_zip_pack_recurse_checkbox, 0, 0, 1, 2)
        layout.addWidget(QLabel("Compression", group), 1, 0)
        layout.addWidget(self.seven_zip_pack_level_combo, 1, 1)
        layout.addWidget(QLabel("Method", group), 2, 0)
        layout.addWidget(self.seven_zip_pack_method_combo, 2, 1)
        layout.addWidget(self.seven_zip_pack_solid_checkbox, 3, 0, 1, 2)
        layout.addWidget(self.seven_zip_pack_header_checkbox, 4, 0, 1, 2)
        layout.addWidget(QLabel("Extra args", group), 5, 0)
        layout.addWidget(self.seven_zip_pack_extra_args_edit, 5, 1)
        layout.setColumnStretch(1, 1)
        return group

    def _build_common_unpack_group(self) -> QWidget:
        group = QWidget(self.options_host)
        layout = QGridLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)

        self.unpack_password_edit = QLineEdit(group)
        self.unpack_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.unpack_password_edit.setPlaceholderText("Optional archive password")

        layout.addWidget(QLabel("Password", group), 0, 0)
        layout.addWidget(self.unpack_password_edit, 0, 1)
        layout.setColumnStretch(1, 1)
        return group

    def _build_winrar_unpack_group(self) -> QWidget:
        group = QWidget(self.options_host)
        layout = QGridLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)

        self.winrar_unpack_mode_combo = QComboBox(group)
        self.winrar_unpack_mode_combo.addItem("Preserve paths", "x")
        self.winrar_unpack_mode_combo.addItem("Flat extract", "e")
        self.winrar_unpack_overwrite_combo = QComboBox(group)
        self.winrar_unpack_overwrite_combo.addItem("Default", "")
        self.winrar_unpack_overwrite_combo.addItem("Overwrite existing", "-o+")
        self.winrar_unpack_overwrite_combo.addItem("Skip existing", "-o-")
        self.winrar_unpack_keep_broken_checkbox = QCheckBox(
            "Keep broken files (-kb)",
            group,
        )
        self.winrar_unpack_extra_args_edit = QLineEdit(group)
        self.winrar_unpack_extra_args_edit.setPlaceholderText(
            "Additional WinRAR unpack args"
        )

        layout.addWidget(QLabel("Extract mode", group), 0, 0)
        layout.addWidget(self.winrar_unpack_mode_combo, 0, 1)
        layout.addWidget(QLabel("Overwrite mode", group), 1, 0)
        layout.addWidget(self.winrar_unpack_overwrite_combo, 1, 1)
        layout.addWidget(self.winrar_unpack_keep_broken_checkbox, 2, 0, 1, 2)
        layout.addWidget(QLabel("Extra args", group), 3, 0)
        layout.addWidget(self.winrar_unpack_extra_args_edit, 3, 1)
        layout.setColumnStretch(1, 1)
        return group

    def _build_seven_zip_unpack_group(self) -> QWidget:
        group = QWidget(self.options_host)
        layout = QGridLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)

        self.seven_zip_unpack_mode_combo = QComboBox(group)
        self.seven_zip_unpack_mode_combo.addItem("Preserve paths", "x")
        self.seven_zip_unpack_mode_combo.addItem("Flat extract", "e")
        self.seven_zip_unpack_overwrite_combo = QComboBox(group)
        self.seven_zip_unpack_overwrite_combo.addItem("Default", "")
        self.seven_zip_unpack_overwrite_combo.addItem("Overwrite existing", "-aoa")
        self.seven_zip_unpack_overwrite_combo.addItem("Skip existing", "-aos")
        self.seven_zip_unpack_overwrite_combo.addItem(
            "Auto rename extracted",
            "-aou",
        )
        self.seven_zip_unpack_extra_args_edit = QLineEdit(group)
        self.seven_zip_unpack_extra_args_edit.setPlaceholderText(
            "Additional 7-Zip unpack args"
        )

        layout.addWidget(QLabel("Extract mode", group), 0, 0)
        layout.addWidget(self.seven_zip_unpack_mode_combo, 0, 1)
        layout.addWidget(QLabel("Overwrite mode", group), 1, 0)
        layout.addWidget(self.seven_zip_unpack_overwrite_combo, 1, 1)
        layout.addWidget(QLabel("Extra args", group), 2, 0)
        layout.addWidget(self.seven_zip_unpack_extra_args_edit, 2, 1)
        layout.setColumnStretch(1, 1)
        return group

    def _set_combo_data(self, combo: QComboBox, target_data: str) -> None:
        for index in range(combo.count()):
            if str(combo.itemData(index)) == str(target_data):
                combo.setCurrentIndex(index)
                return
        combo.setCurrentIndex(0)

    def _selected_backend(self) -> str:
        return str(self.backend_combo.currentData() or "")

    def _selected_dispatch_mode(self) -> str:
        return str(self.dispatch_combo.currentData() or DISPATCH_MODE_QUEUE)

    def _suggest_pack_target_path(self) -> Path:
        backend = self._selected_backend()
        suffix = ".7z" if backend == BACKEND_ARCHIVE_7ZIP else ".rar"
        base_dir = self._sources[0].parent if self._sources else Path.cwd()
        stem = self._sources[0].name if len(self._sources) == 1 else "archive"
        return base_dir / f"{stem}{suffix}"

    def _suggest_unpack_target_dir(self) -> Path:
        archive = self._sources[0] if self._sources else Path.cwd()
        return archive.parent / archive.stem

    def _browse_target(self) -> None:
        if self._kind == "pack":
            backend = self._selected_backend()
            filter_text = (
                "7z Archives (*.7z)"
                if backend == BACKEND_ARCHIVE_7ZIP
                else "RAR Archives (*.rar)"
            )
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Pack Files",
                str(self._validated_pack_target_path()),
                filter_text,
            )
            if path:
                self.target_edit.setText(path)
            return

        directory = QFileDialog.getExistingDirectory(
            self,
            "Unpack Files",
            self.target_edit.text().strip() or str(self._suggest_unpack_target_dir()),
        )
        if directory:
            self.target_edit.setText(directory)

    def _validated_pack_target_path(self) -> Path:
        text = self.target_edit.text().strip()
        target = Path(text) if text else self._suggest_pack_target_path()
        suffix = ".7z" if self._selected_backend() == BACKEND_ARCHIVE_7ZIP else ".rar"
        if target.suffix.casefold() != suffix:
            target = target.with_suffix(suffix)
        return target

    def _pack_password_text(self) -> str:
        return self.pack_password_edit.text().strip()

    def _unpack_password_text(self) -> str:
        return self.unpack_password_edit.text().strip()

    def _sync_password_state(self) -> None:
        has_password = bool(self._pack_password_text())
        self.pack_encrypt_names_checkbox.setEnabled(has_password)
        if not has_password:
            self.pack_encrypt_names_checkbox.setChecked(False)

    def _pack_password_mode_for_backend(self, backend: str) -> str:
        password = self._pack_password_text()
        if not password:
            return ""
        if (
            backend == BACKEND_ARCHIVE_WINRAR
            and self.pack_encrypt_names_checkbox.isChecked()
        ):
            return f"-hp{password}"
        return f"-p{password}"

    def _unpack_password_mode(self) -> str:
        password = self._unpack_password_text()
        if not password:
            return ""
        return f"-p{password}"

    def _pack_volume_mode(self) -> str:
        volume_size = self.pack_split_size_edit.text().strip()
        if not volume_size:
            return ""
        return f"-v{volume_size}"

    def _sync_backend_state(self) -> None:
        backend = self._selected_backend()
        show_winrar = backend == BACKEND_ARCHIVE_WINRAR
        show_seven_zip = backend == BACKEND_ARCHIVE_7ZIP
        self.common_pack_group.setVisible(self._kind == "pack")
        self.common_unpack_group.setVisible(self._kind == "unpack")
        self.winrar_pack_group.setVisible(self._kind == "pack" and show_winrar)
        self.seven_zip_pack_group.setVisible(self._kind == "pack" and show_seven_zip)
        self.winrar_unpack_group.setVisible(self._kind == "unpack" and show_winrar)
        self.seven_zip_unpack_group.setVisible(
            self._kind == "unpack" and show_seven_zip
        )
        if self._kind == "pack":
            self.target_edit.setText(str(self._validated_pack_target_path()))

    def _collect_backend_options(self) -> dict[str, str]:
        backend = self._selected_backend()
        if self._kind == "pack" and backend == BACKEND_ARCHIVE_WINRAR:
            return {
                "recurse_mode": (
                    "-r" if self.winrar_pack_recurse_checkbox.isChecked() else ""
                ),
                "compression_level": str(
                    self.winrar_pack_level_combo.currentData() or ""
                ),
                "solid_mode": (
                    "-s" if self.winrar_pack_solid_checkbox.isChecked() else ""
                ),
                "recovery_mode": (
                    "-rr3p" if self.winrar_pack_recovery_checkbox.isChecked() else ""
                ),
                "lock_mode": (
                    "-k" if self.winrar_pack_lock_checkbox.isChecked() else ""
                ),
                "password_mode": self._pack_password_mode_for_backend(backend),
                "volume_mode": self._pack_volume_mode(),
                "sfx_mode": "-sfx" if self.pack_sfx_checkbox.isChecked() else "",
                "test_mode": "-t" if self.pack_test_checkbox.isChecked() else "",
                "extra_args": self.winrar_pack_extra_args_edit.text().strip(),
            }
        if self._kind == "pack" and backend == BACKEND_ARCHIVE_7ZIP:
            return {
                "recurse_mode": (
                    "-r" if self.seven_zip_pack_recurse_checkbox.isChecked() else ""
                ),
                "compression_level": str(
                    self.seven_zip_pack_level_combo.currentData() or ""
                ),
                "method_mode": str(
                    self.seven_zip_pack_method_combo.currentData() or ""
                ),
                "solid_mode": (
                    "-ms=on" if self.seven_zip_pack_solid_checkbox.isChecked() else ""
                ),
                "header_mode": (
                    "-mhc=on" if self.seven_zip_pack_header_checkbox.isChecked() else ""
                ),
                "password_mode": self._pack_password_mode_for_backend(backend),
                "header_encrypt_mode": (
                    "-mhe=on"
                    if self.pack_encrypt_names_checkbox.isChecked()
                    and bool(self._pack_password_text())
                    else ""
                ),
                "volume_mode": self._pack_volume_mode(),
                "sfx_mode": "-sfx" if self.pack_sfx_checkbox.isChecked() else "",
                "test_mode": "-t" if self.pack_test_checkbox.isChecked() else "",
                "extra_args": self.seven_zip_pack_extra_args_edit.text().strip(),
            }
        if self._kind == "unpack" and backend == BACKEND_ARCHIVE_WINRAR:
            return {
                "extract_mode": str(self.winrar_unpack_mode_combo.currentData() or "x"),
                "overwrite_mode": str(
                    self.winrar_unpack_overwrite_combo.currentData() or ""
                ),
                "keep_broken_mode": (
                    "-kb" if self.winrar_unpack_keep_broken_checkbox.isChecked() else ""
                ),
                "password_mode": self._unpack_password_mode(),
                "extra_args": self.winrar_unpack_extra_args_edit.text().strip(),
            }
        return {
            "extract_mode": str(self.seven_zip_unpack_mode_combo.currentData() or "x"),
            "overwrite_mode": str(
                self.seven_zip_unpack_overwrite_combo.currentData() or ""
            ),
            "password_mode": self._unpack_password_mode(),
            "extra_args": self.seven_zip_unpack_extra_args_edit.text().strip(),
        }

    def selected_result(self) -> ArchiveDialogResult:
        target_path = (
            self._validated_pack_target_path() if self._kind == "pack" else None
        )
        target_dir = (
            Path(self.target_edit.text().strip()) if self._kind == "unpack" else None
        )
        return ArchiveDialogResult(
            backend_id=self._selected_backend(),
            dispatch_mode=self._selected_dispatch_mode(),
            target_dir=target_dir,
            target_path=target_path,
            backend_options=self._collect_backend_options(),
        )

    def build_request(self, *, created_by: str) -> OperationRequest:
        selection = self.selected_result()
        return OperationRequest(
            kind=self._kind,
            sources=tuple(self._sources),
            target_dir=selection.target_dir,
            target_path=selection.target_path,
            backend_id=selection.backend_id,
            dispatch_mode=selection.dispatch_mode,
            conflict_policy=self._preferences.default_operation_conflict_policy,
            backend_options=selection.backend_options,
            created_by=created_by,
        )

    def accept(self) -> None:
        if self._kind == "pack":
            if not self._sources:
                QMessageBox.warning(
                    self,
                    "Pack Files",
                    "Select at least one item first.",
                )
                return
            if not self._validated_pack_target_path().name:
                QMessageBox.warning(
                    self,
                    "Pack Files",
                    "Enter an archive file name.",
                )
                return
        else:
            if len(self._sources) != 1:
                QMessageBox.warning(
                    self,
                    "Unpack Files",
                    "Select exactly one archive to unpack.",
                )
                return
            archive = self._sources[0]
            if archive.suffix.casefold() not in {".rar", ".7z"}:
                QMessageBox.warning(
                    self,
                    "Unpack Files",
                    "Only .rar and .7z archives are supported.",
                )
                return
            if not self.target_edit.text().strip():
                QMessageBox.warning(
                    self,
                    "Unpack Files",
                    "Choose an extraction destination.",
                )
                return
        super().accept()
