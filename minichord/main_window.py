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
from minichord.i18n import install_translations
from minichord.resources import app_icon
from minichord.recovery import RecoveryDraft, RecoveryManager
from minichord.settings import (
    DEFAULT_LANGUAGE,
    THEME_DARK,
    THEME_LIGHT,
    THEME_SYSTEM,
    SettingsManager,
)
from minichord.theme import apply_theme
from minichord.ui.page_editor import MAX_ZOOM, MIN_ZOOM, PageEditor
from minichord.ui.preferences_dialog import PreferencesDialog
from minichord.ui.recovery_dialog import RecoveryDialog


DEFAULT_ZOOM = 1.0
ZOOM_STEP = 0.1


class MainWindow(QMainWindow):
    """Top-level miniChord window with basic file actions."""

    def __init__(
        self,
        settings: SettingsManager | None = None,
        autosave_manager: AutosaveManager | None = None,
        backup_manager: BackupManager | None = None,
        recovery_manager: RecoveryManager | None = None,
        autosave_interval_ms: int = DEFAULT_AUTOSAVE_INTERVAL_MS,
    ):
        super().__init__()
        self.settings = settings or SettingsManager()
        self.autosave_manager = autosave_manager or AutosaveManager()
        self.backup_manager = backup_manager or BackupManager()
        self.recovery_manager = recovery_manager or RecoveryManager(self.autosave_manager)
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
        self._sync_zoom_actions()
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

    def show_preferences_dialog(self) -> None:
        dialog = PreferencesDialog(self.settings.language(), self)
        if dialog.exec() != PreferencesDialog.DialogCode.Accepted:
            return

        language = dialog.selected_language()
        self.settings.set_language(language)
        self.settings.sync()
        app = QApplication.instance()
        if isinstance(app, QApplication):
            install_translations(app, language)
        self._retranslate_ui()
        self.statusBar().showMessage(
            self.tr("Language changed: {language}").format(
                language=self._language_label(language)
            )
        )

    def set_theme(self, theme: str) -> None:
        self.settings.set_theme(theme)
        self.settings.sync()
        self._apply_current_theme()
        self._sync_theme_actions()
        self.statusBar().showMessage(
            self.tr("Theme: {theme}").format(theme=self._theme_label(self.settings.theme()))
        )

    def set_zoom(self, zoom: float) -> None:
        self.editor.set_zoom(zoom)
        self._sync_zoom_actions()
        self._show_zoom_message()

    def zoom_in(self) -> None:
        self.set_zoom(round(self.editor.zoom() + ZOOM_STEP, 2))

    def zoom_out(self) -> None:
        self.set_zoom(round(self.editor.zoom() - ZOOM_STEP, 2))

    def reset_zoom(self) -> None:
        self.set_zoom(DEFAULT_ZOOM)

    def fit_width(self) -> None:
        self.editor.fit_width()
        self._sync_zoom_actions()
        self._show_zoom_message()

    def fit_page(self) -> None:
        self.editor.fit_page()
        self._sync_zoom_actions()
        self._show_zoom_message()

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

    def show_crash_recovery_dialog(self) -> bool:
        """Show recoverable autosave drafts, returning whether one was handled."""
        drafts = self.recovery_manager.autosave_drafts()
        if not drafts:
            return False

        dialog = RecoveryDialog(drafts, self)
        if dialog.exec() != RecoveryDialog.DialogCode.Accepted:
            return False

        draft = dialog.selected_draft()
        if draft is None:
            return False

        if dialog.selected_action() == RecoveryDialog.DISCARD_ACTION:
            self.recovery_manager.discard(draft)
            self.statusBar().showMessage(self.tr("Discarded autosaved draft"))
            return True

        self._recover_draft(draft)
        self.recovery_manager.discard(draft)
        self.statusBar().showMessage(self.tr("Recovered autosaved draft"))
        return True

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

        self.preferences_action = QAction(self.tr("Preferences..."), self)
        self.preferences_action.triggered.connect(self.show_preferences_dialog)

        self.zoom_in_action = QAction(self.tr("Zoom In"), self)
        self.zoom_in_action.setShortcut("Ctrl++")
        self.zoom_in_action.triggered.connect(self.zoom_in)

        self.zoom_out_action = QAction(self.tr("Zoom Out"), self)
        self.zoom_out_action.setShortcut("Ctrl+-")
        self.zoom_out_action.triggered.connect(self.zoom_out)

        self.reset_zoom_action = QAction(self.tr("Actual Size"), self)
        self.reset_zoom_action.setShortcut("Ctrl+0")
        self.reset_zoom_action.triggered.connect(self.reset_zoom)

        self.fit_width_action = QAction(self.tr("Fit Width"), self)
        self.fit_width_action.triggered.connect(self.fit_width)

        self.fit_page_action = QAction(self.tr("Fit Page"), self)
        self.fit_page_action.triggered.connect(self.fit_page)

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
        self.file_menu = self.menuBar().addMenu(self.tr("File"))
        self.file_menu.addAction(self.new_action)
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addAction(self.save_as_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.export_pdf_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.quit_action)

        self.edit_menu = self.menuBar().addMenu(self.tr("Edit"))
        self.edit_menu.addAction(self.preferences_action)

        self.view_menu = self.menuBar().addMenu(self.tr("View"))
        self.zoom_menu = self.view_menu.addMenu(self.tr("Zoom"))
        self.zoom_menu.addAction(self.zoom_in_action)
        self.zoom_menu.addAction(self.zoom_out_action)
        self.zoom_menu.addAction(self.reset_zoom_action)
        self.zoom_menu.addSeparator()
        self.zoom_menu.addAction(self.fit_width_action)
        self.zoom_menu.addAction(self.fit_page_action)
        self.view_menu.addSeparator()
        self.theme_menu = self.view_menu.addMenu(self.tr("Theme"))
        self.theme_menu.addAction(self.system_theme_action)
        self.theme_menu.addAction(self.light_theme_action)
        self.theme_menu.addAction(self.dark_theme_action)

        self.help_menu = self.menuBar().addMenu(self.tr("Help"))
        self.help_menu.addAction(self.about_action)

    def _create_toolbar(self) -> None:
        self.toolbar = QToolBar(self.tr("Main Toolbar"), self)
        self.toolbar.setObjectName("mainToolbar")
        self.toolbar.setMovable(False)
        self.toolbar.addAction(self.new_action)
        self.toolbar.addAction(self.open_action)
        self.toolbar.addAction(self.save_action)
        self.toolbar.addAction(self.export_pdf_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.zoom_out_action)
        self.toolbar.addAction(self.zoom_in_action)
        self.toolbar.addAction(self.fit_width_action)
        self.addToolBar(self.toolbar)

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

    def _sync_zoom_actions(self) -> None:
        current_zoom = self.editor.zoom()
        self.zoom_out_action.setEnabled(current_zoom > MIN_ZOOM)
        self.zoom_in_action.setEnabled(current_zoom < MAX_ZOOM)
        self.reset_zoom_action.setEnabled(abs(current_zoom - DEFAULT_ZOOM) > 0.001)

    def _show_zoom_message(self) -> None:
        self.statusBar().showMessage(
            self.tr("Zoom: {percent}%").format(percent=self._zoom_percent())
        )

    def _zoom_percent(self) -> int:
        return round(self.editor.zoom() * 100)

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

    def _language_label(self, language: str) -> str:
        labels = {
            DEFAULT_LANGUAGE: self.tr("System default"),
            "en": self.tr("English"),
            "es": self.tr("Spanish"),
        }
        return labels.get(language, language)

    def _retranslate_ui(self) -> None:
        self.new_action.setText(self.tr("New"))
        self.open_action.setText(self.tr("Open..."))
        self.save_action.setText(self.tr("Save"))
        self.save_as_action.setText(self.tr("Save As..."))
        self.export_pdf_action.setText(self.tr("Export PDF..."))
        self.quit_action.setText(self.tr("Quit"))
        self.preferences_action.setText(self.tr("Preferences..."))
        self.zoom_in_action.setText(self.tr("Zoom In"))
        self.zoom_out_action.setText(self.tr("Zoom Out"))
        self.reset_zoom_action.setText(self.tr("Actual Size"))
        self.fit_width_action.setText(self.tr("Fit Width"))
        self.fit_page_action.setText(self.tr("Fit Page"))
        self.about_action.setText(self.tr("About miniChord"))
        self.system_theme_action.setText(self.tr("System"))
        self.light_theme_action.setText(self.tr("Light"))
        self.dark_theme_action.setText(self.tr("Dark"))

        self.file_menu.setTitle(self.tr("File"))
        self.edit_menu.setTitle(self.tr("Edit"))
        self.view_menu.setTitle(self.tr("View"))
        self.zoom_menu.setTitle(self.tr("Zoom"))
        self.theme_menu.setTitle(self.tr("Theme"))
        self.help_menu.setTitle(self.tr("Help"))
        self.toolbar.setWindowTitle(self.tr("Main Toolbar"))

        if self.current_path is None:
            self.setWindowTitle(self.tr("miniChord - Untitled"))
        else:
            self.setWindowTitle(self.tr("miniChord - {name}").format(name=self.current_path.name))

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

    def _recover_draft(self, draft: RecoveryDraft) -> None:
        self._set_editor_text_without_autosave(draft.document.text)
        self.current_path = draft.source_path
        self._autosave_draft_id = AutosaveManager.new_draft_id()
        if self.current_path is None:
            self.setWindowTitle(self.tr("miniChord - Recovered Draft"))
        else:
            self.setWindowTitle(self.tr("miniChord - {name}").format(name=self.current_path.name))

    def closeEvent(self, event) -> None:  # noqa: ANN001 - Qt override
        self.perform_autosave()
        self.settings.save_main_window(self)
        super().closeEvent(event)
