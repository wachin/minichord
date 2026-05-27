"""Main window for the initial miniChord prototype."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import PYQT_VERSION_STR, QT_VERSION_STR, QMarginsF, QTimer
from PyQt6.QtGui import QAction, QActionGroup, QPageLayout, QPageSize
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QToolBar,
)

from minichord import __version__
from minichord.autosave import DEFAULT_AUTOSAVE_INTERVAL_MS, AutosaveManager
from minichord.backup import BackupManager
from minichord.document import MiniChordDocument
from minichord.resources import app_icon
from minichord.settings import THEME_DARK, THEME_LIGHT, THEME_SYSTEM, SettingsManager
from minichord.theme import apply_theme
from minichord.ui.page_editor import PageEditor


class MainWindow(QMainWindow):
    """Top-level miniChord window with basic file actions."""

    def __init__(
        self,
        settings: SettingsManager | None = None,
        autosave_manager: AutosaveManager | None = None,
        backup_manager: BackupManager | None = None,
        autosave_interval_ms: int = DEFAULT_AUTOSAVE_INTERVAL_MS,
    ):
        super().__init__()
        self.settings = settings or SettingsManager()
        self.autosave_manager = autosave_manager or AutosaveManager()
        self.backup_manager = backup_manager or BackupManager()
        self._autosave_draft_id = AutosaveManager.new_draft_id()
        self._autosave_dirty = False
        self._autosave_suspended = False
        self._apply_current_theme()
        self.editor = PageEditor()
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(max(1, autosave_interval_ms))
        self._autosave_timer.timeout.connect(self.perform_autosave)
        self.editor.text_document().contentsChanged.connect(self._schedule_autosave)
        self.current_path: Path | None = None
        self.setWindowIcon(app_icon())
        self.setCentralWidget(self.editor)
        self.setWindowTitle(self.tr("miniChord - Untitled"))

        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self._sync_theme_actions()
        self.settings.restore_main_window(self)
        self.statusBar().showMessage(self.tr("Ready"))

    def new_document(self) -> None:
        self._clear_current_autosave()
        self.current_path = None
        self._autosave_draft_id = AutosaveManager.new_draft_id()
        self._set_editor_text_without_autosave("")
        self.setWindowTitle(self.tr("miniChord - Untitled"))
        self.statusBar().showMessage(self.tr("New document"))

    def open_document(self) -> None:
        path_text, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Open miniChord Document"),
            self._file_dialog_directory(),
            self.tr("miniChord Documents (*.mchord);;Text Files (*.txt);;All Files (*)"),
        )
        if path_text:
            self.load_path(Path(path_text))

    def save_document(self) -> None:
        if self.current_path is None:
            self.save_document_as()
            return
        self.save_path(self.current_path)

    def save_document_as(self) -> None:
        path_text, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save miniChord Document"),
            self._file_dialog_directory(),
            self.tr("miniChord Documents (*.mchord);;All Files (*)"),
        )
        if not path_text:
            return
        path = Path(path_text)
        if path.suffix == "":
            path = path.with_suffix(".mchord")
        self.save_path(path)

    def export_pdf(self) -> None:
        path_text, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Export PDF"),
            self._file_dialog_directory(),
            self.tr("PDF Files (*.pdf);;All Files (*)"),
        )
        if not path_text:
            return
        path = Path(path_text)
        if path.suffix == "":
            path = path.with_suffix(".pdf")

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(str(path))
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageMargins(
            QMarginsF(20.0, 20.0, 20.0, 20.0),
            QPageLayout.Unit.Millimeter,
        )
        self.editor.text_document().print(printer)
        self.settings.set_last_directory(path.parent)
        self.statusBar().showMessage(self.tr("Exported PDF: {path}").format(path=path))

    def load_path(self, path: Path) -> None:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, self.tr("Open Failed"), str(exc))
            return

        if path.suffix == ".mchord":
            document = MiniChordDocument.from_mchord(content)
            self._set_editor_text_without_autosave(document.text)
        else:
            self._set_editor_text_without_autosave(content)

        self._clear_current_autosave()
        self.current_path = path
        self.settings.remember_file(path)
        self.setWindowTitle(self.tr("miniChord - {name}").format(name=path.name))
        self.statusBar().showMessage(self.tr("Opened: {path}").format(path=path))

    def save_path(self, path: Path) -> None:
        document = MiniChordDocument(text=self.editor.text())
        previous_path = self.current_path
        previous_draft_id = self._autosave_draft_id
        if path.is_file():
            try:
                self.backup_manager.create_snapshot(path)
            except OSError as exc:
                QMessageBox.critical(self, self.tr("Backup Failed"), str(exc))
                return

        try:
            path.write_text(document.to_mchord(), encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, self.tr("Save Failed"), str(exc))
            return

        self.autosave_manager.clear(previous_path, previous_draft_id)
        self.current_path = path
        self.autosave_manager.clear(self.current_path, self._autosave_draft_id)
        self._autosave_dirty = False
        self._autosave_timer.stop()
        self.settings.remember_file(path)
        self.setWindowTitle(self.tr("miniChord - {name}").format(name=path.name))
        self.statusBar().showMessage(self.tr("Saved: {path}").format(path=path))

    def show_about_dialog(self) -> None:
        QMessageBox.about(self, self.tr("About miniChord"), self._about_text())

    def set_theme(self, theme: str) -> None:
        self.settings.set_theme(theme)
        self.settings.sync()
        self._apply_current_theme()
        self._sync_theme_actions()
        self.statusBar().showMessage(
            self.tr("Theme: {theme}").format(theme=self._theme_label(self.settings.theme()))
        )

    def perform_autosave(self, force: bool = False) -> Path | None:
        """Write a crash-recovery draft when the document has pending edits."""
        self._autosave_timer.stop()
        if not force and not self._autosave_dirty:
            return None

        text = self.editor.text()
        if self.current_path is None and not text.strip():
            self._clear_current_autosave()
            return None

        try:
            draft = self.autosave_manager.write(
                MiniChordDocument(text=text),
                source_path=self.current_path,
                draft_id=self._autosave_draft_id,
            )
        except OSError as exc:
            self.statusBar().showMessage(
                self.tr("Autosave failed: {error}").format(error=exc)
            )
            return None

        self._autosave_dirty = False
        self.statusBar().showMessage(self.tr("Autosaved draft"))
        return draft.path

    def _about_text(self) -> str:
        return self.tr(
            "<h2>miniChord {version}</h2>"
            "<p>A lightweight WYSIWYG ChordPro-oriented word processor.</p>"
            "<p>Designed for page layout, worship songs, and Git-friendly music documents.</p>"
            "<p><b>Qt:</b> {qt_version}<br><b>PyQt:</b> {pyqt_version}</p>"
        ).format(
            version=__version__,
            qt_version=QT_VERSION_STR,
            pyqt_version=PYQT_VERSION_STR,
        )

    def _create_actions(self) -> None:
        self.new_action = QAction(self.tr("New"), self)
        self.new_action.setShortcut("Ctrl+N")
        self.new_action.triggered.connect(self.new_document)

        self.open_action = QAction(self.tr("Open..."), self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self.open_document)

        self.save_action = QAction(self.tr("Save"), self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_document)

        self.save_as_action = QAction(self.tr("Save As..."), self)
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.save_as_action.triggered.connect(self.save_document_as)

        self.export_pdf_action = QAction(self.tr("Export PDF..."), self)
        self.export_pdf_action.triggered.connect(self.export_pdf)

        self.quit_action = QAction(self.tr("Quit"), self)
        self.quit_action.setShortcut("Ctrl+Q")
        self.quit_action.triggered.connect(self.close)

        self.about_action = QAction(self.tr("About miniChord"), self)
        self.about_action.triggered.connect(self.show_about_dialog)

        self.theme_action_group = QActionGroup(self)
        self.theme_action_group.setExclusive(True)

        self.system_theme_action = self._create_theme_action(
            self.tr("System"),
            THEME_SYSTEM,
        )
        self.light_theme_action = self._create_theme_action(
            self.tr("Light"),
            THEME_LIGHT,
        )
        self.dark_theme_action = self._create_theme_action(
            self.tr("Dark"),
            THEME_DARK,
        )

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu(self.tr("File"))
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.export_pdf_action)
        file_menu.addSeparator()
        file_menu.addAction(self.quit_action)

        view_menu = self.menuBar().addMenu(self.tr("View"))
        theme_menu = view_menu.addMenu(self.tr("Theme"))
        theme_menu.addAction(self.system_theme_action)
        theme_menu.addAction(self.light_theme_action)
        theme_menu.addAction(self.dark_theme_action)

        help_menu = self.menuBar().addMenu(self.tr("Help"))
        help_menu.addAction(self.about_action)

    def _create_toolbar(self) -> None:
        toolbar = QToolBar(self.tr("Main Toolbar"), self)
        toolbar.setObjectName("mainToolbar")
        toolbar.setMovable(False)
        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addAction(self.export_pdf_action)
        self.addToolBar(toolbar)

    def _file_dialog_directory(self) -> str:
        directory = self.settings.last_directory()
        if directory is None:
            return ""
        return str(directory)

    def _create_theme_action(self, label: str, theme: str) -> QAction:
        action = QAction(label, self)
        action.setCheckable(True)
        action.setData(theme)
        action.triggered.connect(lambda checked=False, selected=theme: self.set_theme(selected))
        self.theme_action_group.addAction(action)
        return action

    def _sync_theme_actions(self) -> None:
        current_theme = self.settings.theme()
        for action in self.theme_action_group.actions():
            action.setChecked(action.data() == current_theme)

    def _apply_current_theme(self) -> None:
        app = QApplication.instance()
        if isinstance(app, QApplication):
            apply_theme(app, self.settings.theme())

    def _theme_label(self, theme: str) -> str:
        labels = {
            THEME_SYSTEM: self.tr("System"),
            THEME_LIGHT: self.tr("Light"),
            THEME_DARK: self.tr("Dark"),
        }
        return labels.get(theme, labels[THEME_SYSTEM])

    def _schedule_autosave(self) -> None:
        if self._autosave_suspended:
            return

        self._autosave_dirty = True
        self._autosave_timer.start()

    def _set_editor_text_without_autosave(self, text: str) -> None:
        self._autosave_suspended = True
        try:
            self.editor.set_text(text)
        finally:
            self._autosave_suspended = False
        self._autosave_dirty = False
        self._autosave_timer.stop()

    def _clear_current_autosave(self) -> None:
        self.autosave_manager.clear(self.current_path, self._autosave_draft_id)
        self._autosave_dirty = False
        self._autosave_timer.stop()

    def closeEvent(self, event) -> None:  # noqa: ANN001 - Qt override
        self.perform_autosave()
        self.settings.save_main_window(self)
        super().closeEvent(event)
