"""Main window for the initial ChordPages prototype."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import PYQT_VERSION_STR, QT_VERSION_STR, QMarginsF, QSizeF, QTimer
from PyQt6.QtGui import (
    QAction,
    QActionGroup,
    QDragEnterEvent,
    QDropEvent,
    QFont,
    QKeySequence,
    QPageLayout,
    QPageSize,
)
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QFileDialog,
    QFontComboBox,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QToolBar,
)

from chordpages import __version__
from chordpages.autosave import DEFAULT_AUTOSAVE_INTERVAL_MS, AutosaveManager
from chordpages.backup import BackupManager
from chordpages.document import ChordPagesDocument
from chordpages.document.text_file import (
    TextFileInfo,
    detect_file_type,
    read_text_file,
    write_text_file,
)
from chordpages.document.transpose import transpose_text
from chordpages.fonts import default_editor_font, make_editor_font
from chordpages.i18n import install_translations
from chordpages.resources import app_icon
from chordpages.recovery import RecoveryDraft, RecoveryManager
from chordpages.settings import (
    DEFAULT_LANGUAGE,
    THEME_DARK,
    THEME_LIGHT,
    THEME_SYSTEM,
    SettingsManager,
)
from chordpages.theme import apply_theme
from chordpages.ui.page_editor import (
    MAX_ZOOM,
    MIN_ZOOM,
    MULTIPLE_PAGE_VIEW_COLUMNS,
    PageEditor,
    SINGLE_PAGE_VIEW_COLUMNS,
)
from chordpages.ui.preferences_dialog import PreferencesDialog
from chordpages.ui.recovery_dialog import RecoveryDialog


DEFAULT_ZOOM = 1.0
ZOOM_STEP = 0.1
DEFAULT_ENCODING = "utf-8"
DEFAULT_NEWLINE = "\n"
DEFAULT_FILE_TYPE = "text"


@dataclass(slots=True)
class DocumentTab:
    editor: PageEditor
    path: Path | None = None
    encoding: str = DEFAULT_ENCODING
    newline: str = DEFAULT_NEWLINE
    file_type: str = DEFAULT_FILE_TYPE
    modified: bool = False
    autosave_draft_id: str = ""


class MainWindow(QMainWindow):
    """Top-level ChordPages window with basic file actions."""

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
        self._editor_font = self._load_editor_font()
        self.current_path: Path | None = None
        self.use_sharps = True
        self._apply_current_theme()
        self._documents: dict[PageEditor, DocumentTab] = {}
        self.tabs = QTabWidget()
        self.tabs.setObjectName("documentTabs")
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.currentChanged.connect(self._handle_current_tab_changed)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setAcceptDrops(True)
        self.add_document_tab()
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(max(1, autosave_interval_ms))
        self._autosave_timer.timeout.connect(self.perform_autosave)
        self.setWindowIcon(app_icon())
        self.setCentralWidget(self.tabs)
        self.setWindowTitle(self.tr("ChordPages - Untitled"))

        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self._sync_theme_actions()
        self._sync_zoom_actions()
        self._sync_page_view_actions()
        self._sync_font_controls()
        self.settings.restore_main_window(self)
        self.statusBar().showMessage(self.tr("Ready"))

    @property
    def editor(self) -> PageEditor:
        widget = self.tabs.currentWidget()
        if isinstance(widget, PageEditor):
            return widget
        return self.add_document_tab()

    def current_document(self) -> DocumentTab:
        editor = self.editor
        return self._documents[editor]

    def add_document_tab(
        self,
        text: str = "",
        path: Path | None = None,
        file_info: TextFileInfo | None = None,
    ) -> PageEditor:
        editor = PageEditor(editor_font=self._editor_font)
        editor.textChanged.connect(lambda editor=editor: self._handle_editor_text_changed(editor))
        metadata = DocumentTab(
            editor=editor,
            path=path,
            encoding=file_info.encoding if file_info else DEFAULT_ENCODING,
            newline=file_info.newline if file_info else DEFAULT_NEWLINE,
            file_type=file_info.file_type if file_info else (
                detect_file_type(path) if path else DEFAULT_FILE_TYPE
            ),
            autosave_draft_id=AutosaveManager.new_draft_id(),
        )
        self._documents[editor] = metadata
        self._set_tab_text_without_autosave(editor, text)
        tab_index = self.tabs.addTab(editor, self._tab_label(metadata))
        self.tabs.setCurrentIndex(tab_index)
        return editor

    def close_tab(self, index: int) -> None:
        if self.tabs.count() <= 1:
            editor = self.editor
            metadata = self.current_document()
            self.autosave_manager.clear(metadata.path, metadata.autosave_draft_id)
            metadata.path = None
            metadata.encoding = DEFAULT_ENCODING
            metadata.newline = DEFAULT_NEWLINE
            metadata.file_type = DEFAULT_FILE_TYPE
            metadata.modified = False
            metadata.autosave_draft_id = AutosaveManager.new_draft_id()
            self._set_tab_text_without_autosave(editor, "")
            self.current_path = None
            self._refresh_tab_label(editor)
            self._update_window_title()
            return
        editor = self.tabs.widget(index)
        if not isinstance(editor, PageEditor):
            return
        metadata = self._documents.pop(editor, None)
        if metadata is not None:
            self.autosave_manager.clear(metadata.path, metadata.autosave_draft_id)
        self.tabs.removeTab(index)
        editor.deleteLater()
        self._handle_current_tab_changed(self.tabs.currentIndex())

    def _handle_current_tab_changed(self, _index: int) -> None:
        metadata = self.current_document()
        self.current_path = metadata.path
        self._autosave_draft_id = metadata.autosave_draft_id
        self._autosave_dirty = metadata.modified
        if hasattr(self, "zoom_in_action"):
            self._sync_zoom_actions()
        if hasattr(self, "single_page_view_action"):
            self._sync_page_view_actions()
        if hasattr(self, "font_family_combo"):
            self._sync_font_controls()
        self._update_window_title()
        self._show_file_metadata_message()

    def _handle_editor_text_changed(self, editor: PageEditor) -> None:
        if self._autosave_suspended:
            return
        metadata = self._documents.get(editor)
        if metadata is None:
            return
        metadata.modified = True
        self._refresh_tab_label(editor)
        if editor is self.editor:
            self._schedule_autosave()

    def _tab_label(self, metadata: DocumentTab) -> str:
        label = metadata.path.name if metadata.path else self.tr("Untitled")
        return f"*{label}" if metadata.modified else label

    def _refresh_tab_label(self, editor: PageEditor) -> None:
        index = self.tabs.indexOf(editor)
        if index >= 0:
            self.tabs.setTabText(index, self._tab_label(self._documents[editor]))

    def _current_tab_can_be_reused_for_open(self) -> bool:
        metadata = self.current_document()
        return (
            self.tabs.count() == 1
            and metadata.path is None
            and not metadata.modified
            and self.editor.text() == ""
        )

    def _set_tab_text_without_autosave(self, editor: PageEditor, text: str) -> None:
        self._autosave_suspended = True
        try:
            editor.set_text(text)
        finally:
            self._autosave_suspended = False

    def _update_window_title(self) -> None:
        metadata = self.current_document()
        if metadata.path is None:
            self.setWindowTitle(self.tr("ChordPages - Untitled"))
        else:
            self.setWindowTitle(self.tr("ChordPages - {name}").format(name=metadata.path.name))

    def _show_file_metadata_message(self) -> None:
        metadata = self.current_document()
        self.statusBar().showMessage(
            self.tr("Type: {type} | Encoding: {encoding} | Line endings: {newline}").format(
                type=metadata.file_type,
                encoding=metadata.encoding,
                newline=self._newline_label(metadata.newline),
            )
        )

    @staticmethod
    def _newline_label(newline: str) -> str:
        return {
            "\n": "LF",
            "\r\n": "CRLF",
            "\r": "CR",
        }.get(newline, repr(newline))

    def new_document(self) -> None:
        self.add_document_tab()
        self.setWindowTitle(self.tr("ChordPages - Untitled"))
        self.statusBar().showMessage(self.tr("New document"))

    def open_document(self) -> None:
        path_texts, _ = QFileDialog.getOpenFileNames(
            self,
            self.tr("Open ChordPages Document"),
            self._file_dialog_directory(),
            self.tr(
                "Supported Files (*.mchord *.txt *.pro *.cho *.chord *.chordpro *.md);;"
                "ChordPages Documents (*.mchord);;"
                "Text and Chord Files (*.txt *.pro *.cho *.chord *.chordpro *.md);;"
                "All Files (*)"
            ),
        )
        for path_text in path_texts:
            self.load_path(Path(path_text))

    def save_document(self) -> None:
        if self.current_path is None:
            self.save_document_as()
            return
        self.save_path(self.current_path)

    def save_document_as(self) -> None:
        path_text, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save ChordPages Document"),
            self._file_dialog_directory(),
            self.tr(
                "Text Files (*.txt);;"
                "ChordPro Files (*.pro *.cho *.chord *.chordpro);;"
                "ChordPages Documents (*.mchord);;"
                "All Files (*)"
            ),
        )
        if not path_text:
            return
        path = Path(path_text)
        if path.suffix == "":
            path = path.with_suffix(".txt")
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
        page_layout = self.editor.page_layout()
        page_width_mm, page_height_mm = page_layout.size_mm
        margins = page_layout.effective_margins()
        printer.setPageSize(
            QPageSize(
                QSizeF(page_width_mm, page_height_mm),
                QPageSize.Unit.Millimeter,
                page_layout.page_size,
            )
        )
        printer.setPageMargins(
            QMarginsF(margins.left, margins.top, margins.right, margins.bottom),
            QPageLayout.Unit.Millimeter,
        )
        self.editor.text_document().print(printer)
        self.settings.set_last_directory(path.parent)
        self.statusBar().showMessage(self.tr("Exported PDF: {path}").format(path=path))

    def load_path(self, path: Path) -> None:
        try:
            file_info = read_text_file(path)
        except OSError as exc:
            QMessageBox.critical(self, self.tr("Open Failed"), str(exc))
            return

        if file_info.file_type == "chordpages":
            document = ChordPagesDocument.from_mchord(file_info.text)
            text = document.text
        else:
            text = file_info.text

        resolved_path = path.resolve(strict=False)
        if self._current_tab_can_be_reused_for_open():
            editor = self.editor
            metadata = self._documents[editor]
            metadata.path = resolved_path
            metadata.encoding = file_info.encoding
            metadata.newline = file_info.newline
            metadata.file_type = file_info.file_type
            self._set_tab_text_without_autosave(editor, text)
        else:
            editor = self.add_document_tab(text=text, path=resolved_path, file_info=file_info)
            metadata = self._documents[editor]
        metadata.modified = False
        self._refresh_tab_label(editor)
        self.current_path = metadata.path
        self.settings.remember_file(path)
        self._update_window_title()
        self.statusBar().showMessage(
            self.tr("Opened: {path} ({type}, {encoding}, {newline})").format(
                path=path,
                type=metadata.file_type,
                encoding=metadata.encoding,
                newline=self._newline_label(metadata.newline),
            )
        )

    def save_path(self, path: Path) -> None:
        metadata = self.current_document()
        previous_path = metadata.path
        previous_draft_id = metadata.autosave_draft_id
        if path.is_file():
            try:
                self.backup_manager.create_snapshot(path)
            except OSError as exc:
                QMessageBox.critical(self, self.tr("Backup Failed"), str(exc))
                return

        try:
            if detect_file_type(path) == "chordpages":
                document = ChordPagesDocument(text=self.editor.text())
                write_text_file(path, document.to_mchord(), "utf-8", "\n")
                metadata.file_type = "chordpages"
                metadata.encoding = "utf-8"
                metadata.newline = "\n"
            else:
                metadata.file_type = detect_file_type(path)
                write_text_file(
                    path,
                    self.editor.text(),
                    metadata.encoding or DEFAULT_ENCODING,
                    metadata.newline or DEFAULT_NEWLINE,
                )
        except OSError as exc:
            QMessageBox.critical(self, self.tr("Save Failed"), str(exc))
            return

        self.autosave_manager.clear(previous_path, previous_draft_id)
        metadata.path = path.resolve(strict=False)
        self.current_path = metadata.path
        self.autosave_manager.clear(metadata.path, metadata.autosave_draft_id)
        metadata.modified = False
        self._refresh_tab_label(self.editor)
        self._autosave_dirty = False
        self._autosave_timer.stop()
        self.settings.remember_file(path)
        self._update_window_title()
        self.statusBar().showMessage(
            self.tr("Saved: {path} ({type}, {encoding}, {newline})").format(
                path=path,
                type=metadata.file_type,
                encoding=metadata.encoding,
                newline=self._newline_label(metadata.newline),
            )
        )

    def show_about_dialog(self) -> None:
        QMessageBox.about(self, self.tr("About ChordPages"), self._about_text())

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

    def set_editor_font_family(self, font: QFont) -> None:
        self.set_editor_font(
            make_editor_font(
                font.family(),
                self._editor_font.pointSizeF(),
            )
        )

    def set_editor_font_size(self, point_size: float) -> None:
        self.set_editor_font(
            make_editor_font(
                self._editor_font.family(),
                point_size,
            )
        )

    def set_editor_font(self, font: QFont) -> None:
        self._editor_font = QFont(font)
        for editor in self._documents:
            editor.set_editor_font(self._editor_font)

        self.settings.set_editor_font_family(self._editor_font.family())
        self.settings.set_editor_font_size(self._editor_font.pointSizeF())
        self.settings.sync()
        self._sync_font_controls()
        self.statusBar().showMessage(
            self.tr("Font: {family} {size} pt").format(
                family=self._editor_font.family(),
                size=self._font_size_label(),
            )
        )

    def fit_width(self) -> None:
        self.editor.fit_width()
        self._sync_zoom_actions()
        self._show_zoom_message()

    def fit_page(self) -> None:
        self.editor.fit_page()
        self._sync_zoom_actions()
        self._show_zoom_message()

    def transpose_up(self) -> None:
        self.transpose_current_document(1)

    def transpose_down(self) -> None:
        self.transpose_current_document(-1)

    def transpose_current_document(self, semitones: int) -> None:
        if semitones == 0:
            return
        current_text = self.editor.text()
        transposed = transpose_text(current_text, semitones, use_sharps=self.use_sharps)
        if transposed == current_text:
            self.statusBar().showMessage(self.tr("No chords found to transpose"))
            return
        self._set_tab_text_without_autosave(self.editor, transposed)
        self._handle_editor_text_changed(self.editor)
        self.statusBar().showMessage(
            self.tr("Transposed chords: {semitones:+d}").format(semitones=semitones)
        )

    def set_transpose_accidentals(self, use_sharps: bool) -> None:
        self.use_sharps = use_sharps
        self.use_sharps_action.setChecked(use_sharps)
        self.use_flats_action.setChecked(not use_sharps)

    def set_pages_per_row(self, pages_per_row: int) -> None:
        self.editor.set_pages_per_row(pages_per_row)
        self._sync_page_view_actions()
        self.statusBar().showMessage(
            self.tr("Page view: {view}").format(
                view=self._page_view_label(pages_per_row)
            )
        )

    def set_single_page_view(self) -> None:
        self.set_pages_per_row(SINGLE_PAGE_VIEW_COLUMNS)

    def set_multiple_page_view(self) -> None:
        self.set_pages_per_row(MULTIPLE_PAGE_VIEW_COLUMNS)

    def perform_autosave(self, force: bool = False) -> Path | None:
        """Write a crash-recovery draft when the document has pending edits."""
        self._autosave_timer.stop()
        metadata = self.current_document()
        self.current_path = metadata.path
        self._autosave_draft_id = metadata.autosave_draft_id
        self._autosave_dirty = metadata.modified
        if not force and not self._autosave_dirty:
            return None

        text = self.editor.text()
        if self.current_path is None and not text.strip():
            self._clear_current_autosave()
            return None

        try:
            draft = self.autosave_manager.write(
                ChordPagesDocument(text=text),
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
            "<h2>ChordPages {version}</h2>"
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
        self.zoom_in_action.setShortcuts([QKeySequence("Ctrl++"), QKeySequence("Ctrl+=")])
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

        self.page_view_action_group = QActionGroup(self)
        self.page_view_action_group.setExclusive(True)

        self.single_page_view_action = QAction(self.tr("Single Page"), self)
        self.single_page_view_action.setCheckable(True)
        self.single_page_view_action.triggered.connect(self.set_single_page_view)
        self.page_view_action_group.addAction(self.single_page_view_action)

        self.multiple_page_view_action = QAction(self.tr("Multiple Pages"), self)
        self.multiple_page_view_action.setCheckable(True)
        self.multiple_page_view_action.triggered.connect(self.set_multiple_page_view)
        self.page_view_action_group.addAction(self.multiple_page_view_action)

        self.transpose_up_action = QAction(self.tr("Transpose Up"), self)
        self.transpose_up_action.setShortcut("Ctrl+Up")
        self.transpose_up_action.triggered.connect(self.transpose_up)

        self.transpose_down_action = QAction(self.tr("Transpose Down"), self)
        self.transpose_down_action.setShortcut("Ctrl+Down")
        self.transpose_down_action.triggered.connect(self.transpose_down)

        self.transpose_step_actions: list[QAction] = []
        for semitones in range(-7, 8):
            label = self.tr("{semitones:+d} semitones").format(semitones=semitones)
            if semitones == 0:
                label = self.tr("Original")
            action = QAction(label, self)
            action.triggered.connect(
                lambda checked=False, value=semitones: self.transpose_current_document(value)
            )
            self.transpose_step_actions.append(action)

        self.accidental_action_group = QActionGroup(self)
        self.accidental_action_group.setExclusive(True)
        self.use_sharps_action = QAction(self.tr("Use Sharps"), self)
        self.use_sharps_action.setCheckable(True)
        self.use_sharps_action.setChecked(True)
        self.use_sharps_action.triggered.connect(lambda: self.set_transpose_accidentals(True))
        self.accidental_action_group.addAction(self.use_sharps_action)

        self.use_flats_action = QAction(self.tr("Use Flats"), self)
        self.use_flats_action.setCheckable(True)
        self.use_flats_action.triggered.connect(lambda: self.set_transpose_accidentals(False))
        self.accidental_action_group.addAction(self.use_flats_action)

        self.about_action = QAction(self.tr("About ChordPages"), self)
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

        self.transpose_menu = self.menuBar().addMenu(self.tr("Transpose"))
        self.transpose_menu.addAction(self.transpose_down_action)
        self.transpose_menu.addAction(self.transpose_up_action)
        self.transpose_menu.addSeparator()
        for action in self.transpose_step_actions:
            self.transpose_menu.addAction(action)
        self.transpose_menu.addSeparator()
        self.transpose_menu.addAction(self.use_sharps_action)
        self.transpose_menu.addAction(self.use_flats_action)

        self.view_menu = self.menuBar().addMenu(self.tr("View"))
        self.page_view_menu = self.view_menu.addMenu(self.tr("Page View"))
        self.page_view_menu.addAction(self.single_page_view_action)
        self.page_view_menu.addAction(self.multiple_page_view_action)
        self.view_menu.addSeparator()
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
        self.toolbar.addAction(self.transpose_down_action)
        self.toolbar.addAction(self.transpose_up_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.zoom_out_action)
        self.toolbar.addAction(self.zoom_in_action)
        self.toolbar.addAction(self.fit_width_action)
        self.toolbar.addSeparator()
        self.font_family_combo = QFontComboBox(self.toolbar)
        self.font_family_combo.setObjectName("fontFamilyComboBox")
        self.font_family_combo.setFontFilters(
            QFontComboBox.FontFilter.MonospacedFonts
        )
        self.font_family_combo.setMaximumWidth(220)
        self.font_family_combo.setToolTip(self.tr("Font family"))
        self.font_family_combo.currentFontChanged.connect(self.set_editor_font_family)
        self.toolbar.addWidget(self.font_family_combo)

        self.font_size_spin = QDoubleSpinBox(self.toolbar)
        self.font_size_spin.setObjectName("fontSizeSpinBox")
        self.font_size_spin.setDecimals(1)
        self.font_size_spin.setRange(4.0, 72.0)
        self.font_size_spin.setSingleStep(0.5)
        self.font_size_spin.setSuffix(" pt")
        self.font_size_spin.setToolTip(self.tr("Font size"))
        self.font_size_spin.valueChanged.connect(self.set_editor_font_size)
        self.toolbar.addWidget(self.font_size_spin)
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

    def _sync_page_view_actions(self) -> None:
        pages_per_row = self.editor.pages_per_row()
        self.single_page_view_action.setChecked(
            pages_per_row == SINGLE_PAGE_VIEW_COLUMNS
        )
        self.multiple_page_view_action.setChecked(
            pages_per_row == MULTIPLE_PAGE_VIEW_COLUMNS
        )

    def _sync_font_controls(self) -> None:
        if not hasattr(self, "font_family_combo"):
            return

        font_signals_blocked = self.font_family_combo.blockSignals(True)
        size_signals_blocked = self.font_size_spin.blockSignals(True)
        try:
            self.font_family_combo.setCurrentFont(self._editor_font)
            self.font_size_spin.setValue(self._editor_font.pointSizeF())
        finally:
            self.font_family_combo.blockSignals(font_signals_blocked)
            self.font_size_spin.blockSignals(size_signals_blocked)

    def _show_zoom_message(self) -> None:
        self.statusBar().showMessage(
            self.tr("Zoom: {percent}%").format(percent=self._zoom_percent())
        )

    def _zoom_percent(self) -> int:
        return round(self.editor.zoom() * 100)

    def _font_size_label(self) -> str:
        return f"{self._editor_font.pointSizeF():g}"

    def _load_editor_font(self) -> QFont:
        fallback_font = default_editor_font()
        return make_editor_font(
            self.settings.editor_font_family(fallback_font.family()),
            self.settings.editor_font_size(fallback_font.pointSizeF()),
        )

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

    def _page_view_label(self, pages_per_row: int) -> str:
        labels = {
            SINGLE_PAGE_VIEW_COLUMNS: self.tr("Single Page"),
            MULTIPLE_PAGE_VIEW_COLUMNS: self.tr("Multiple Pages"),
        }
        return labels.get(
            pages_per_row,
            self.tr("{count} pages per row").format(count=pages_per_row),
        )

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
        self.single_page_view_action.setText(self.tr("Single Page"))
        self.multiple_page_view_action.setText(self.tr("Multiple Pages"))
        self.about_action.setText(self.tr("About ChordPages"))
        self.system_theme_action.setText(self.tr("System"))
        self.light_theme_action.setText(self.tr("Light"))
        self.dark_theme_action.setText(self.tr("Dark"))

        self.file_menu.setTitle(self.tr("File"))
        self.edit_menu.setTitle(self.tr("Edit"))
        self.transpose_menu.setTitle(self.tr("Transpose"))
        self.view_menu.setTitle(self.tr("View"))
        self.page_view_menu.setTitle(self.tr("Page View"))
        self.zoom_menu.setTitle(self.tr("Zoom"))
        self.theme_menu.setTitle(self.tr("Theme"))
        self.help_menu.setTitle(self.tr("Help"))
        self.toolbar.setWindowTitle(self.tr("Main Toolbar"))
        self.font_family_combo.setToolTip(self.tr("Font family"))
        self.font_size_spin.setToolTip(self.tr("Font size"))

        if self.current_path is None:
            self.setWindowTitle(self.tr("ChordPages - Untitled"))
        else:
            self.setWindowTitle(self.tr("ChordPages - {name}").format(name=self.current_path.name))

    def _schedule_autosave(self) -> None:
        if self._autosave_suspended:
            return

        metadata = self.current_document()
        metadata.modified = True
        self._autosave_draft_id = metadata.autosave_draft_id
        self.current_path = metadata.path
        self._autosave_dirty = True
        self._autosave_timer.start()

    def _set_editor_text_without_autosave(self, text: str) -> None:
        self._set_tab_text_without_autosave(self.editor, text)
        self._autosave_dirty = False
        self._autosave_timer.stop()

    def _clear_current_autosave(self) -> None:
        metadata = self.current_document()
        self.autosave_manager.clear(metadata.path, metadata.autosave_draft_id)
        metadata.modified = False
        self._refresh_tab_label(metadata.editor)
        self._autosave_dirty = False
        self._autosave_timer.stop()

    def _recover_draft(self, draft: RecoveryDraft) -> None:
        editor = self.add_document_tab(
            text=draft.document.text,
            path=draft.source_path,
            file_info=None,
        )
        metadata = self._documents[editor]
        metadata.file_type = detect_file_type(draft.source_path) if draft.source_path else "chordpages"
        metadata.modified = True
        self.current_path = metadata.path
        self._autosave_draft_id = metadata.autosave_draft_id
        self._refresh_tab_label(editor)
        self._update_window_title()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        paths = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        if not paths:
            super().dropEvent(event)
            return
        for path in paths:
            if path.is_file():
                self.load_path(path)
        event.acceptProposedAction()

    def closeEvent(self, event) -> None:  # noqa: ANN001 - Qt override
        current_index = self.tabs.currentIndex()
        for index in range(self.tabs.count()):
            self.tabs.setCurrentIndex(index)
            self.perform_autosave()
        self.tabs.setCurrentIndex(current_index)
        self.settings.save_main_window(self)
        super().closeEvent(event)
