"""Main window for the initial miniChord prototype."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QMarginsF
from PyQt6.QtGui import QAction, QPageLayout, QPageSize
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QToolBar,
)

from minichord.document import MiniChordDocument
from minichord.ui.page_editor import PageEditor


class MainWindow(QMainWindow):
    """Top-level miniChord window with basic file actions."""

    def __init__(self):
        super().__init__()
        self.editor = PageEditor()
        self.current_path: Path | None = None
        self.setCentralWidget(self.editor)
        self.setWindowTitle(self.tr("miniChord - Untitled"))
        self.resize(1100, 850)

        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self.statusBar().showMessage(self.tr("Ready"))

    def new_document(self) -> None:
        self.current_path = None
        self.editor.set_text("")
        self.setWindowTitle(self.tr("miniChord - Untitled"))
        self.statusBar().showMessage(self.tr("New document"))

    def open_document(self) -> None:
        path_text, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Open miniChord Document"),
            "",
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
            "",
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
            "",
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
        self.statusBar().showMessage(self.tr("Exported PDF: {path}").format(path=path))

    def load_path(self, path: Path) -> None:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, self.tr("Open Failed"), str(exc))
            return

        if path.suffix == ".mchord":
            document = MiniChordDocument.from_mchord(content)
            self.editor.set_text(document.text)
        else:
            self.editor.set_text(content)

        self.current_path = path
        self.setWindowTitle(self.tr("miniChord - {name}").format(name=path.name))
        self.statusBar().showMessage(self.tr("Opened: {path}").format(path=path))

    def save_path(self, path: Path) -> None:
        document = MiniChordDocument(text=self.editor.text())
        try:
            path.write_text(document.to_mchord(), encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, self.tr("Save Failed"), str(exc))
            return

        self.current_path = path
        self.setWindowTitle(self.tr("miniChord - {name}").format(name=path.name))
        self.statusBar().showMessage(self.tr("Saved: {path}").format(path=path))

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

    def _create_toolbar(self) -> None:
        toolbar = QToolBar(self.tr("Main Toolbar"), self)
        toolbar.setMovable(False)
        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addAction(self.export_pdf_action)
        self.addToolBar(toolbar)
