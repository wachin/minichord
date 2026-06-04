import sys
import os
import math
import re
import json
import chardet
from PyQt6.QtGui import (QFont, QAction, QActionGroup, QDragEnterEvent, QDropEvent, QTextCursor,
                         QShortcut, QKeySequence, QTextDocument, QColor)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QLabel, QSlider, QFileDialog, QMenuBar,
    QMenu, QMessageBox, QInputDialog, QFontDialog, QTabWidget,
    QDialog, QLineEdit, QCheckBox, QGridLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QListWidget, QListWidgetItem,
    QComboBox
)
from PyQt6.QtCore import (
    Qt, QTimer, QUrl, QTranslator, QLocale, QLibraryInfo,
    QRegularExpression
)

class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(False)  # Desactivar el manejo de drops por defecto


class FindInFilesDialog(QDialog):
    """
    Búsqueda/Reemplazo en archivos (recursiva con filtros).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.setWindowTitle("Buscar en archivos")
        self.resize(700, 520)

        layout = QVBoxLayout(self)

        form = QGridLayout()
        layout.addLayout(form)

        form.addWidget(QLabel("Carpeta:"), 0, 0)
        self.dir_edit = QLineEdit(os.getcwd())
        form.addWidget(self.dir_edit, 0, 1)
        btn_browse = QPushButton("Examinar…")
        form.addWidget(btn_browse, 0, 2)

        form.addWidget(QLabel("Patrones (sep. por ;):"), 1, 0)
        self.patterns = QLineEdit("*.txt;*.md;*.chord;*.pro")
        form.addWidget(self.patterns, 1, 1, 1, 2)

        form.addWidget(QLabel("Buscar:"), 2, 0)
        self.find_edit = QLineEdit()
        form.addWidget(self.find_edit, 2, 1, 1, 2)

        form.addWidget(QLabel("Reemplazar con:"), 3, 0)
        self.replace_edit = QLineEdit()
        form.addWidget(self.replace_edit, 3, 1, 1, 2)

        opts = QHBoxLayout()
        layout.addLayout(opts)
        self.case_cb = QCheckBox("Mayúsculas/minúsculas")
        self.word_cb = QCheckBox("Palabra completa")
        self.regex_cb = QCheckBox("Usar expresiones regulares")
        self.recursive_cb = QCheckBox("Buscar recursivamente")
        self.recursive_cb.setChecked(True)
        opts.addWidget(self.case_cb)
        opts.addWidget(self.word_cb)
        opts.addWidget(self.regex_cb)
        opts.addWidget(self.recursive_cb)
        opts.addStretch(1)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Archivo", "Línea", "Col", "Vista previa"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        btns = QHBoxLayout()
        layout.addLayout(btns)
        self.btn_search = QPushButton("Buscar")
        self.btn_replace_sel = QPushButton("Reemplazar en archivos")
        self.btn_close = QPushButton("Cerrar")
        btns.addWidget(self.btn_search)
        btns.addWidget(self.btn_replace_sel)
        btns.addStretch(1)
        btns.addWidget(self.btn_close)

        btn_browse.clicked.connect(self._browse)
        self.btn_search.clicked.connect(self._do_search)
        self.btn_replace_sel.clicked.connect(self._do_replace_all)
        self.btn_close.clicked.connect(self.close)
        self.table.cellDoubleClicked.connect(self._open_match)

    def _browse(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Elegir carpeta", self.dir_edit.text() or os.getcwd()
        )
        if directory:
            self.dir_edit.setText(directory)

    def _iter_files(self, root, patterns, recursive=True):
        import fnmatch
        pats = [p.strip() for p in patterns.split(";") if p.strip()]
        if not pats:
            pats = ["*"]

        if recursive:
            for base, _dirs, files in os.walk(root):
                for name in files:
                    if any(fnmatch.fnmatch(name, pat) for pat in pats):
                        yield os.path.join(base, name)
        else:
            for name in os.listdir(root):
                file_path = os.path.join(root, name)
                if os.path.isfile(file_path) and any(fnmatch.fnmatch(name, pat) for pat in pats):
                    yield file_path

    def _compile(self, text):
        flags = 0
        if not self.case_cb.isChecked():
            flags |= re.IGNORECASE

        pattern = text if self.regex_cb.isChecked() else re.escape(text)
        if self.word_cb.isChecked():
            pattern = r"\b" + pattern + r"\b"
        return re.compile(pattern, flags)

    def _do_search(self):
        self.table.setRowCount(0)
        root = self.dir_edit.text().strip() or os.getcwd()
        query = self.find_edit.text()
        if not query:
            return

        try:
            rx = self._compile(query)
        except re.error as e:
            QMessageBox.warning(self, "Expresión inválida", str(e))
            return

        for file_path in self._iter_files(root, self.patterns.text(), self.recursive_cb.isChecked()):
            try:
                with open(file_path, "rb") as file:
                    raw = file.read()
                encoding = chardet.detect(raw).get("encoding") or "utf-8"
                text = raw.decode(encoding, errors="ignore")
            except Exception:
                continue

            for line_number, line in enumerate(text.splitlines(), start=1):
                for match in rx.finditer(line):
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(file_path))
                    self.table.setItem(row, 1, QTableWidgetItem(str(line_number)))
                    self.table.setItem(row, 2, QTableWidgetItem(str(match.start() + 1)))
                    self.table.setItem(row, 3, QTableWidgetItem(line.strip()))

    def _do_replace_all(self):
        root = self.dir_edit.text().strip() or os.getcwd()
        query = self.find_edit.text()
        replacement = self.replace_edit.text()
        if not query:
            return

        try:
            rx = self._compile(query)
        except re.error as e:
            QMessageBox.warning(self, "Expresión inválida", str(e))
            return

        count_total = 0
        files_changed = 0
        for file_path in self._iter_files(root, self.patterns.text(), self.recursive_cb.isChecked()):
            try:
                with open(file_path, "rb") as file:
                    raw = file.read()
                encoding = chardet.detect(raw).get("encoding") or "utf-8"
                text = raw.decode(encoding, errors="ignore")
                new_text, count = rx.subn(replacement, text)
                if count > 0:
                    with open(file_path, "w", encoding=encoding, newline="") as out:
                        out.write(new_text)
                    count_total += count
                    files_changed += 1
            except Exception:
                continue

        QMessageBox.information(
            self,
            "Reemplazo en archivos",
            f"Reemplazos: {count_total}\nArchivos modificados: {files_changed}"
        )

    def _open_match(self, row, _col):
        file_path = self.table.item(row, 0).text()
        line = int(self.table.item(row, 1).text())
        col = int(self.table.item(row, 2).text())
        self.parent_widget.open_file_at(file_path, line, col)


class MythesThesaurus:
    def __init__(self):
        self.languages = self._find_languages()
        self.cache = {}

    def _find_languages(self):
        labels = {
            "es": "Español (Ecuador)",
            "de": "Alemán",
            "en": "Inglés (Estados Unidos)",
        }
        best_by_path = {}
        search_dirs = [
            "/usr/share/mythes",
            "/usr/share/hunspell",
            "/usr/share/myspell/dicts",
        ]

        for base in search_dirs:
            if not os.path.isdir(base):
                continue
            for name in sorted(os.listdir(base)):
                if not (name.startswith("th_") and name.endswith(".dat")):
                    continue
                dat_path = os.path.join(base, name)
                idx_path = dat_path[:-4] + ".idx"
                if not os.path.exists(idx_path):
                    continue
                code = name[3:-4]
                if code.endswith("_v2"):
                    code = code[:-3]
                key = os.path.realpath(dat_path)
                lang = code.split("_")[0]
                label = labels.get(lang, code.replace("_", "-"))
                language = {
                    "code": code,
                    "label": label,
                    "dat": dat_path,
                }
                current = best_by_path.get(key)
                if current is None or self._language_priority(code) < self._language_priority(current["code"]):
                    best_by_path[key] = language

        languages = list(best_by_path.values())
        languages.sort(key=lambda item: (item["code"] != "es_ES", item["label"]))
        return languages

    def _language_priority(self, code):
        if code == "es_ES":
            return 0
        if code == "es_EC":
            return 1
        if code.startswith("es_"):
            return 2
        return 3

    def _read_entries(self, language):
        dat_path = language["dat"]
        if dat_path in self.cache:
            return self.cache[dat_path]

        entries = {}
        with open(dat_path, "rb") as file:
            raw = file.read()

        first_line, _, body = raw.partition(b"\n")
        encoding = first_line.decode("ascii", errors="ignore").strip() or "ISO8859-1"
        text = body.decode(encoding, errors="replace")
        lines = iter(text.splitlines())

        for line in lines:
            if "|" not in line:
                continue
            word, count_text = line.split("|", 1)
            try:
                count = int(count_text)
            except ValueError:
                continue

            groups = []
            for _ in range(count):
                try:
                    group_line = next(lines)
                except StopIteration:
                    break
                parts = [part.strip() for part in group_line.split("|") if part.strip()]
                if parts and parts[0] == "-":
                    parts = parts[1:]
                if parts:
                    groups.append(parts)

            entries[word.casefold()] = groups

        self.cache[dat_path] = entries
        return entries

    def lookup(self, word, language_index=0):
        if not word or not self.languages:
            return []
        language = self.languages[language_index]
        entries = self._read_entries(language)
        return entries.get(word.casefold(), [])

    def language_label(self, language_index=0):
        if not self.languages:
            return "Sin diccionario Mythes"
        return self.languages[language_index]["label"]


class SynonymsDialog(QDialog):
    def __init__(self, parent, word, language_index=0):
        super().__init__(parent)
        self.parent_widget = parent
        self.word = word
        self.language_index = language_index
        self.setWindowTitle(f"Sinónimos ({self.parent_widget.thesaurus.language_label(language_index)})")
        self.resize(560, 430)

        layout = QVBoxLayout(self)

        form = QGridLayout()
        layout.addLayout(form)

        form.addWidget(QLabel("Palabra actual:"), 0, 1)

        back_button = QPushButton("←")
        back_button.setEnabled(False)
        form.addWidget(back_button, 1, 0)

        self.word_edit = QLineEdit(word)
        self.word_edit.returnPressed.connect(self.refresh_results)
        form.addWidget(self.word_edit, 1, 1)

        search_button = QPushButton("▼")
        search_button.clicked.connect(self.refresh_results)
        form.addWidget(search_button, 1, 2)

        self.language_combo = QComboBox()
        for language in self.parent_widget.thesaurus.languages:
            self.language_combo.addItem(language["label"])
        if self.parent_widget.thesaurus.languages:
            self.language_combo.setCurrentIndex(language_index)
        self.language_combo.currentIndexChanged.connect(self.change_language)
        form.addWidget(self.language_combo, 1, 3)

        layout.addWidget(QLabel("Alternativas:"))

        self.results = QListWidget()
        self.results.itemClicked.connect(self.select_synonym)
        self.results.itemDoubleClicked.connect(self.replace_selected)
        layout.addWidget(self.results, 1)

        layout.addWidget(QLabel("Reemplazar por:"))
        self.replace_edit = QLineEdit()
        layout.addWidget(self.replace_edit)

        buttons = QHBoxLayout()
        layout.addLayout(buttons)
        help_button = QPushButton("Ayuda")
        help_button.clicked.connect(self.show_help)
        buttons.addWidget(help_button)
        buttons.addStretch(1)

        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(cancel_button)

        replace_button = QPushButton("Reemplazar")
        replace_button.clicked.connect(self.replace_selected)
        buttons.addWidget(replace_button)

        self.refresh_results()

    def change_language(self, index):
        self.language_index = index
        self.setWindowTitle(f"Sinónimos ({self.parent_widget.thesaurus.language_label(index)})")
        self.refresh_results()

    def refresh_results(self):
        self.results.clear()
        self.word = self.word_edit.text().strip()
        groups = self.parent_widget.thesaurus.lookup(self.word, self.language_index)

        if not groups:
            item = QListWidgetItem("No se encontraron sinónimos")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.results.addItem(item)
            self.replace_edit.clear()
            return

        first_synonym = ""
        for index, group in enumerate(groups, start=1):
            header_text = f"{index}. - {group[0]}"
            header = QListWidgetItem(header_text)
            font = header.font()
            font.setBold(True)
            header.setFont(font)
            header.setFlags(Qt.ItemFlag.NoItemFlags)
            self.results.addItem(header)

            for synonym in group:
                item = QListWidgetItem(synonym)
                item.setData(Qt.ItemDataRole.UserRole, synonym)
                self.results.addItem(item)
                if not first_synonym:
                    first_synonym = synonym

        self.replace_edit.setText(first_synonym)
        if self.results.count() > 1:
            self.results.setCurrentRow(1)

    def select_synonym(self, item):
        synonym = item.data(Qt.ItemDataRole.UserRole)
        if synonym:
            self.replace_edit.setText(synonym)

    def replace_selected(self):
        replacement = self.replace_edit.text()
        if not replacement:
            return
        self.parent_widget.replace_selected_word(replacement)
        self.accept()

    def show_help(self):
        QMessageBox.information(
            self,
            "Sinónimos",
            "Selecciona una alternativa y pulsa Reemplazar para cambiar la palabra seleccionada."
        )


class TextScrollerApp(QMainWindow):
# Dentro de la clase `TextScrollerApp`
    def show_about_dialog(self):
        about_text = (
            "<h2><b>Chord autoscroll</b></h2>"
            "<p>Este programa sirve para la transposición de acordes, podrás cargar tus canciones que contengan "
            "letras y acordes para transportarlas fácilmente y desplazarte automáticamente por el texto, "
            "para tus ensayos.</p>"
            "<p>Copyright 2025  Washington Indacochea Delgado.<br>"
            "wachin.id@gmail.com<br>"
            "Licencia GPL 3</p>"
            "<p>Para más información revisa:</p>"
            '<a href="https://github.com/wachin/py_chord_autoscroll">https://github.com/wachin/py_chord_autoscroll</a>'
        )

        dialog = QMessageBox(self)
        dialog.setWindowTitle("Acerca de Chord Autoscroll")
        dialog.setTextFormat(Qt.TextFormat.RichText)  # Permitir formato HTML
        dialog.setText(about_text)
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        dialog.exec()

    def __init__(self):
        super().__init__()
        self.translator = QTranslator()

        translations_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
        print(f"Ruta de traducciones: {translations_path}")  # Depuración

        # Cargar traducción al español
        if self.translator.load("qtbase_es", translations_path):
            QApplication.installTranslator(self.translator)
            print("Traducción al español cargada correctamente.")
        else:
            print("No se pudo cargar la traducción al español.")

        self.setWindowTitle("Lector y Editor de Letras con Acordes")
        self.setGeometry(100, 100, 800, 500)

        self.current_file = None
        self.is_scrolling = False
        self.max_speed = 400  # Velocidad máxima predeterminada
        self.scroll_speed = self.calculate_speed(15)  # Velocidad predeterminada

        self.config_file = 'config12.json'

        self.opened_files = {}  # Diccionario para rutas de archivos
        self.file_encodings = {}  # Diccionario para guardar codificaciones

        # Inicializar configuración antes de usarla
        self.config = {}
        self.load_config()
        self.thesaurus = MythesThesaurus()

        # Diccionario para rastrear archivos abiertos en pestañas
        self.opened_files = {}

        self.init_ui()

        self.replace_btn.clicked.connect(self.replace_one)
        self.replace_all_btn.clicked.connect(self.replace_all)

        # Actualizar el menú "Abrir reciente" después de cargar la configuración
        self.update_recent_files_menu()

    def select_font(self):
        # Abrir diálogo de selección de fuente
        font, ok = QFontDialog.getFont(QFont(self.config.get('font_family', 'Noto Mono'),
                                            self.config.get('font_size', 10)),
                                    self, "Selecciona una fuente")

        # Si el usuario selecciona una fuente y presiona OK
        if ok:
            # Aplicar la fuente seleccionada al área de texto
            current_widget = self.get_current_text_widget()
            if current_widget:
                current_widget.setFont(font)

            # Guardar la fuente seleccionada en la configuración
            self.config['font_family'] = font.family()
            self.config['font_size'] = font.pointSize()
            self.save_config()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Contenedor de pestañas
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        layout.addWidget(self.tab_widget)

        # Crear la primera pestaña
        self.add_new_tab()

        # Controles para desplazamiento y transposición
        control_layout = QHBoxLayout()
        layout.addLayout(control_layout)

        self.start_button = QPushButton("Iniciar")
        self.start_button.clicked.connect(self.start_scrolling)
        control_layout.addWidget(self.start_button)

        self.pause_button = QPushButton("Pausar")
        self.pause_button.clicked.connect(self.pause_scrolling)
        control_layout.addWidget(self.pause_button)

        control_layout.addWidget(QLabel("Velocidad:"))

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 30)

        # Restaurar la posición del deslizador desde la configuración
        last_position = self.config.get('last_slider_position', 15)
        self.speed_slider.setValue(last_position)

        # Recalcular la velocidad al iniciar el programa
        self.update_speed()

        self.speed_slider.valueChanged.connect(self.update_speed)
        control_layout.addWidget(self.speed_slider)

        self.transpose_button = QPushButton("Transponer")
        self.transpose_button.clicked.connect(self.show_transpose_menu)
        control_layout.addWidget(self.transpose_button)
        
        # Añadir etiqueta para mostrar la codificación
        self.encoding_label = QLabel("Codificación: UTF-8")
        self.encoding_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.encoding_label)

        self.create_menu_bar()

        # Crear el atajo de teclado para iniciar/pausar el scroll
        shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
        shortcut.activated.connect(self.toggle_scroll)

        self.tab_widget.currentChanged.connect(self.update_encoding_label)  # Conectar evento

        self.setAcceptDrops(True)

        # =========================
        # Panel de Buscar / Reemplazar
        # =========================

        self.search_panel = QWidget()
        self.search_panel.setVisible(False)  # empieza oculto

        search_layout = QVBoxLayout(self.search_panel)

        # ---- Buscar ----
        find_layout = QHBoxLayout()

        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Buscar")

        self.find_prev_btn = QPushButton("Anterior")
        self.find_next_btn = QPushButton("Siguiente")

        # Conexiones
        self.find_next_btn.clicked.connect(self.find_next)
        self.find_prev_btn.clicked.connect(self.find_previous)
        self.find_input.returnPressed.connect(self.find_next)

        # Añadir al layout
        find_layout.addWidget(QLabel("Buscar:"))
        find_layout.addWidget(self.find_input)
        find_layout.addWidget(self.find_prev_btn)
        find_layout.addWidget(self.find_next_btn)

        search_layout.addLayout(find_layout)

        # Opciones
        options_layout = QHBoxLayout()

        self.match_case_cb = QCheckBox("Coincidir mayúsculas")
        self.regex_cb = QCheckBox("Expresiones regulares")

        options_layout.addWidget(self.match_case_cb)
        options_layout.addWidget(self.regex_cb)

        search_layout.addLayout(options_layout)

        # ---- Reemplazar ----
        replace_layout = QHBoxLayout()

        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Reemplazar")

        self.replace_btn = QPushButton("Reemplazar")
        self.replace_all_btn = QPushButton("Reemplazar todo")

        self.replace_label = QLabel("Reemplazar:")
        replace_layout.addWidget(self.replace_label)
        replace_layout.addWidget(self.replace_input)
        replace_layout.addWidget(self.replace_btn)
        replace_layout.addWidget(self.replace_all_btn)

        search_layout.addLayout(replace_layout)

        # Reemplazar oculto al inicio
        self.replace_label.setVisible(False)
        self.replace_input.setVisible(False)
        self.replace_btn.setVisible(False)
        self.replace_all_btn.setVisible(False)

        # Añadir panel al layout principal
        layout.addWidget(self.search_panel)

    def find_previous(self):
        editor = self.get_current_text_widget()
        if not editor:
            return

        text = self.find_input.text()
        if not text:
            return

        flags = QTextDocument.FindFlag.FindBackward

        if self.match_case_cb.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        found = editor.find(text, flags)

        # Si llega al inicio, vuelve al final
        if not found:
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            editor.setTextCursor(cursor)
            editor.find(text, flags)

    def replace_one(self):
        editor = self.get_current_text_widget()
        if not editor:
            return

        cursor = editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.replace_input.text())
            self.find_next()

    def replace_all(self):
        editor = self.get_current_text_widget()
        if not editor:
            return

        text = editor.toPlainText()
        find = self.find_input.text()
        replace = self.replace_input.text()

        if self.regex_cb.isChecked():
            flags = 0 if self.match_case_cb.isChecked() else re.IGNORECASE
            text = re.sub(find, replace, text, flags=flags)
        else:
            if self.match_case_cb.isChecked():
                text = text.replace(find, replace)
            else:
                text = re.sub(re.escape(find), replace, text, flags=re.IGNORECASE)

        editor.setPlainText(text)

    def highlight_all_matches(self):
        editor = self.get_current_text_widget()
        if not editor:
            return

        text = self.find_input.text()
        if not text:
            editor.setExtraSelections([])
            return

        cursor = editor.textCursor()
        cursor.beginEditBlock()

        selections = []

        doc = editor.document()
        flags = QTextDocument.FindFlag(0)

        if self.match_case_cb.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        # Empezar desde el inicio del documento
        cursor = QTextCursor(doc)
        while True:
            if self.regex_cb.isChecked():
                pattern = QRegularExpression(text)
                cursor = doc.find(pattern, cursor)
            else:
                cursor = doc.find(text, cursor, flags)

            if cursor.isNull():
                break

            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format.setBackground(QColor("#fff59d"))  # amarillo suave
            selections.append(selection)

        editor.setExtraSelections(selections)
        cursor.endEditBlock()

    def update_encoding_label(self, index):
        print(f"Actualizando etiqueta para la pestaña {index}")
        file_path = self.opened_files.get(index, None)
        if file_path and file_path in self.file_encodings:
            encoding = self.file_encodings[file_path]['encoding']
            line_ending = self.file_encodings[file_path]['line_ending']
            self.encoding_label.setText(f"Codificación: {encoding} | Terminador de línea: {line_ending}")

            # Actualizar el título de la ventana con el nombre del archivo
            self.setWindowTitle(f"{os.path.basename(file_path)} - Lector y Editor de Texto con acordes")
        else:
            self.encoding_label.setText("Codificación: N/A | Terminador de línea: N/A")
            self.setWindowTitle("Lector y Editor de Texto con acordes")

    def show_find_panel(self):
        self.search_panel.setVisible(True)

        self.replace_label.setVisible(False)
        self.replace_input.setVisible(False)
        self.replace_btn.setVisible(False)
        self.replace_all_btn.setVisible(False)

        self.find_input.setFocus()

    def show_replace_panel(self):
        self.search_panel.setVisible(True)

        self.replace_label.setVisible(True)
        self.replace_input.setVisible(True)
        self.replace_btn.setVisible(True)
        self.replace_all_btn.setVisible(True)

        self.find_input.setFocus()

    def toggle_scroll(self):
        if self.is_scrolling:
            self.pause_scrolling()
        else:
            self.start_scrolling()

    def find_next(self):
        self.highlight_all_matches()

        editor = self.get_current_text_widget()
        if not editor:
            return

        flags = QTextDocument.FindFlag(0)

        if self.match_case_cb.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        text = self.find_input.text()
        if not text:
            return

        if self.regex_cb.isChecked():
            pattern = QRegularExpression(text)
            editor.find(pattern)
        else:
            editor.find(text, flags)

    def add_new_tab(self, file_name=None, content="", file_path=None):
        # Crear un nuevo área de texto
        text_widget = CustomTextEdit()
        text_widget.setUndoRedoEnabled(True)
        text_widget.document().setModified(False)  # Inicialmente no modificado

        text_widget.textChanged.connect(self.on_text_changed)

        # Aplicar la fuente predeterminada desde la configuración
        default_font = self.config.get('font_family', 'Noto Mono')
        default_font_size = self.config.get('font_size', 10)
        text_widget.setFont(QFont(default_font, default_font_size))

        # Cargar contenido si se proporciona
        if content:
            text_widget.setPlainText(content)
            text_widget.document().setModified(False)  # Marcar como no modificado

        # Agregar el área de texto como nueva pestaña
        tab_name = file_name if file_name else "Nuevo archivo"
        index = self.tab_widget.addTab(text_widget, tab_name)

        # Asociar la pestaña con la ruta del archivo (si existe)
        if file_path:
            self.opened_files[index] = file_path
        else:
            self.opened_files[index] = None

        # Establecer como la pestaña activa
        self.tab_widget.setCurrentWidget(text_widget)

        # Actualizar el título de la ventana
        self.update_window_title()

    def on_text_changed(self):
        current_widget = self.get_current_text_widget()
        if current_widget:
            current_index = self.tab_widget.currentIndex()
            file_path = self.opened_files.get(current_index, None)

            # Verificar que el archivo exista en la lista de archivos abiertos
            if file_path:
                encoding = self.file_encodings.get(file_path, {}).get('encoding', 'utf-8')  # Obtener la codificación

                try:
                    # Leer el contenido guardado del archivo
                    with open(file_path, 'r', encoding=encoding) as f:
                        saved_content = f.read()
                except Exception as e:
                    saved_content = ""  # Si ocurre un error al leer, asumir contenido vacío

                # Obtener el contenido actual del widget
                current_content = current_widget.toPlainText()

                # Comparar ambos para verificar si realmente ha sido modificado
                is_modified = current_content != saved_content
                current_widget.document().setModified(is_modified)

                # Actualizar el título de la ventana
                self.update_window_title()

    def update_window_title(self):
        # Obtener el índice de la pestaña activa
        current_index = self.tab_widget.currentIndex()

        # Obtener el nombre del archivo asociado a la pestaña activa
        file_path = self.opened_files.get(current_index, "Nuevo archivo")
        file_name = os.path.basename(file_path) if file_path else "Nuevo archivo"

        # Verificar si el documento tiene cambios no guardados
        modified = "*" if self.get_current_text_widget().document().isModified() else ""

        # Actualizar el título de la ventana
        self.setWindowTitle(f"{file_name} {modified} - Lector y Editor de Letras con Acordes")

    def close_tab(self, index):
        # Obtener el área de texto de la pestaña
        current_widget = self.tab_widget.widget(index)
        if isinstance(current_widget, CustomTextEdit) and current_widget.document().isModified():
            # Mostrar cuadro de diálogo
            reply = QMessageBox.question(
                self, "Cerrar documento",
                f'El documento "{self.tab_widget.tabText(index)}" ha sido modificado. '
                "¿Desea guardar los cambios, o descartarlos?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                self.tab_widget.setCurrentIndex(index)
                self.save_file()  # Guardar cambios
            elif reply == QMessageBox.StandardButton.Cancel:
                return  # No cerrar la pestaña

        # Cerrar la pestaña
        self.tab_widget.removeTab(index)

    def closeEvent(self, event):
        for index in range(self.tab_widget.count()):
            self.tab_widget.setCurrentIndex(index)
            current_widget = self.tab_widget.widget(index)
            if isinstance(current_widget, CustomTextEdit) and current_widget.document().isModified():
                reply = QMessageBox.question(
                    self, "Cerrar aplicación",
                    f'El documento "{self.tab_widget.tabText(index)}" ha sido modificado. '
                    "¿Desea guardar los cambios, o descartarlos?",
                    QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
                )
                if reply == QMessageBox.StandardButton.Save:
                    self.save_file()
                elif reply == QMessageBox.StandardButton.Cancel:
                    event.ignore()
                    return

        event.accept()

    def get_current_text_widget(self):
        # Obtener el área de texto de la pestaña activa
        widget = self.tab_widget.currentWidget()
        if isinstance(widget, CustomTextEdit):
            return widget
        return None

        # Nueva función: Copiar
    def copy_text(self):
        current_widget = self.get_current_text_widget()
        if current_widget:
            current_widget.copy()

        # Nueva función: Pegar
    def paste_text(self):
        current_widget = self.get_current_text_widget()
        if current_widget:
            current_widget.paste()

    def cut_text(self):
        current_widget = self.get_current_text_widget()
        if current_widget:
            current_widget.cut()

    def create_menu_bar(self):
        menu_bar = self.menuBar()

        # Menú Archivo
        file_menu = menu_bar.addMenu("Archivo")

        new_action = QAction("Nuevo archivo", self)
        new_action.triggered.connect(self.add_new_tab)
        new_action.setShortcut("Ctrl+N")  # Atajo: Ctrl+N
        file_menu.addAction(new_action)

        open_action = QAction("Abrir", self)
        open_action.triggered.connect(self.open_file)
        open_action.setShortcut("Ctrl+O")  # Atajo: Ctrl+O
        file_menu.addAction(open_action)

        # Menú Abrir reciente
        recent_menu = file_menu.addMenu("Abrir reciente")
        self.recent_menu = recent_menu  # Guardar referencia al menú para actualizarlo

        save_action = QAction("Guardar", self)
        save_action.triggered.connect(self.save_file)
        save_action.setShortcut("Ctrl+S")  # Atajo: Ctrl+S
        file_menu.addAction(save_action)

        save_as_action = QAction("Guardar como", self)
        save_as_action.triggered.connect(self.save_file_as_original)  # Llama a save_file_as en lugar de save_file
        save_as_action.setShortcut("Ctrl+Shift+S")  # Atajo: Ctrl+Shift+S
        file_menu.addAction(save_as_action)

        # Opción Guardar Codificación como
        save_as_encoding_action = QAction("Guardar Codificación como...", self)
        save_as_encoding_action.triggered.connect(self.save_file_with_encoding)
        file_menu.addAction(save_as_encoding_action)

        file_menu.addSeparator()

        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut("Ctrl+Q")  # Atajo: Ctrl+Q
        file_menu.addAction(exit_action)

        # Menú Editar
        edit_menu = menu_bar.addMenu("Editar")

        undo_action = QAction("Deshacer", self)
        undo_action.triggered.connect(lambda: self.get_current_text_widget().undo())
        undo_action.setShortcut("Ctrl+Z")  # Atajo: Ctrl+Z
        edit_menu.addAction(undo_action)

        redo_action = QAction("Rehacer", self)
        redo_action.triggered.connect(lambda: self.get_current_text_widget().redo())
        redo_action.setShortcut("Ctrl+Shift+Z")  # Atajo: Ctrl+Shift+Z
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        find_action = QAction("Buscar", self)
        find_action.setShortcut("Ctrl+F")
        find_action.triggered.connect(self.show_find_panel)
        edit_menu.addAction(find_action)

        replace_action = QAction("Reemplazar", self)
        replace_action.setShortcut("Ctrl+H")
        replace_action.triggered.connect(self.show_replace_panel)
        edit_menu.addAction(replace_action)

        find_in_files_action = QAction("Buscar/Reemplazar en archivos…", self)
        find_in_files_action.setShortcut("Ctrl+Shift+F")
        find_in_files_action.triggered.connect(self.show_find_in_files_dialog)
        edit_menu.addAction(find_in_files_action)

        # Añadir un separador
        edit_menu.addSeparator()

        # Nueva opción: Copiar
        copy_action = QAction("Copiar", self)
        copy_action.triggered.connect(self.copy_text)
        copy_action.setShortcut("Ctrl+C")  # Atajo de teclado: Ctrl+C
        edit_menu.addAction(copy_action)

        # Nueva opción: Pegar
        paste_action = QAction("Pegar", self)
        paste_action.triggered.connect(self.paste_text)
        paste_action.setShortcut("Ctrl+V")  # Atajo de teclado: Ctrl+V
        edit_menu.addAction(paste_action)

        # Nueva opción: Cortar

        cut_action = QAction("Cortar", self)
        cut_action.triggered.connect(self.cut_text)
        cut_action.setShortcut("Ctrl+X")  # Atajo de teclado: Ctrl+X
        edit_menu.addAction(cut_action)

        select_all_action = QAction("Seleccionar todo", self)
        select_all_action.triggered.connect(lambda: self.get_current_text_widget().selectAll())
        select_all_action.setShortcut("Ctrl+A")  # Atajo: Ctrl+A
        edit_menu.addAction(select_all_action)

        # Menú Herramientas
        tools_menu = menu_bar.addMenu("Herramientas")

        synonyms_action = QAction("Sinónimos...", self)
        synonyms_action.setShortcut("Ctrl+F7")
        synonyms_action.triggered.connect(self.show_synonyms_dialog)
        tools_menu.addAction(synonyms_action)

        # Menú Opciones
        options_menu = menu_bar.addMenu("Opciones")

        # Opción para usar sostenidos
        sharps_action = QAction("Usar Sostenidos al bajar semitonos", self)
        sharps_action.setCheckable(True)
        sharps_action.setChecked(self.config['use_sharps'])
        sharps_action.triggered.connect(lambda: self.toggle_accidentals(True))
        options_menu.addAction(sharps_action)

        # Opción para usar bemoles
        flats_action = QAction("Usar Bemoles al bajar semitonos", self)
        flats_action.setCheckable(True)
        flats_action.setChecked(not self.config['use_sharps'])
        flats_action.triggered.connect(lambda: self.toggle_accidentals(False))
        options_menu.addAction(flats_action)

        # Añadir un separador
        options_menu.addSeparator()

        # Agrupar las opciones para que sean mutuamente excluyentes
        group = QActionGroup(self)
        group.addAction(sharps_action)
        group.addAction(flats_action)

        # ... Opción de cambiar la fuente
        change_font_action = QAction("Cambiar fuente", self)
        change_font_action.triggered.connect(self.select_font)
        change_font_action.setShortcut("Ctrl+Alt+F")
        options_menu.addAction(change_font_action)

        # ... Opción de cambiar la velocidad máxima
        change_speed_action = QAction("Cambiar velocidad máxima", self)
        change_speed_action.triggered.connect(self.change_max_speed)
        change_speed_action.setShortcut("Ctrl+Shift+V")
        options_menu.addAction(change_speed_action)

        # Menú Ayuda
        help_menu = menu_bar.addMenu("Ayuda")

        about_action = QAction("Acerca de...", self)
        about_action.triggered.connect(self.show_about_dialog)
        about_action.setShortcut("Ctrl+H")
        help_menu.addAction(about_action)

    def selected_word_for_synonyms(self):
        text_widget = self.get_current_text_widget()
        if not text_widget:
            return ""

        cursor = text_widget.textCursor()
        selected = cursor.selectedText().strip()
        if selected:
            return selected

        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        selected = cursor.selectedText().strip()
        if selected:
            text_widget.setTextCursor(cursor)
        return selected

    def show_synonyms_dialog(self):
        if not self.thesaurus.languages:
            QMessageBox.warning(
                self,
                "Sinónimos",
                "No se encontraron diccionarios Mythes en /usr/share/mythes."
            )
            return

        word = self.selected_word_for_synonyms()
        if not word:
            QMessageBox.information(self, "Sinónimos", "Selecciona una palabra para buscar sinónimos.")
            return

        dialog = SynonymsDialog(self, word)
        dialog.exec()

    def replace_selected_word(self, replacement):
        text_widget = self.get_current_text_widget()
        if not text_widget:
            return

        cursor = text_widget.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)

        cursor.insertText(replacement)
        text_widget.setTextCursor(cursor)
        text_widget.setFocus()

    def show_find_in_files_dialog(self):
        try:
            self._fif_dialog.show()
            self._fif_dialog.raise_()
            self._fif_dialog.activateWindow()
            return
        except AttributeError:
            pass

        self._fif_dialog = FindInFilesDialog(self)
        self._fif_dialog.show()

    def open_file_at(self, file_path: str, line: int, col: int):
        """Abre un archivo y posiciona el cursor en la línea/columna dadas (1-based)."""
        self.open_dropped_file(file_path)
        text_widget = self.get_current_text_widget()
        if not text_widget:
            return

        line = max(1, line)
        block = text_widget.document().findBlockByLineNumber(line - 1)
        if not block.isValid():
            return

        cursor = text_widget.textCursor()
        cursor.setPosition(block.position() + max(0, col - 1))
        text_widget.setTextCursor(cursor)
        text_widget.setFocus()

    def update_recent_files_menu(self):
        self.recent_menu.clear()
        recent_files = self.config.get('recent_files', [])

        for entry in recent_files:
            file_path = entry['path']
            timestamp = entry['timestamp']

            # Acción con el nombre y la fecha
            action = QAction(f"{os.path.basename(file_path)} - {timestamp}", self)
            action.triggered.connect(lambda checked, path=file_path: self.open_recent_file(path))
            self.recent_menu.addAction(action)

            # Acción separadora para mostrar la ruta completa como texto no clicable
            path_action = QAction(f"Ruta: {file_path}", self)
            path_action.setEnabled(False)  # Deshabilitar para que no sea clicable
            self.recent_menu.addAction(path_action)

        if not recent_files:
            self.recent_menu.addAction("No hay archivos recientes").setEnabled(False)

    def open_recent_file(self, file_path):
        if os.path.exists(file_path):
            self.open_dropped_file(file_path)
        else:
            QMessageBox.warning(self, "Error", f"El archivo '{file_path}' no existe.")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            file_path = url.toLocalFile()
            self.open_dropped_file(file_path)
            event.acceptProposedAction()
        else:
            event.ignore()

    def open_dropped_file(self, file_path):
        if os.path.exists(file_path) and file_path.lower().endswith('.txt'):
            try:
                # Detectar la codificación del archivo
                with open(file_path, 'rb') as file:
                    raw_data = file.read()
                    detected = chardet.detect(raw_data)
                    encoding = detected['encoding'] or 'utf-8'

                # Detectar terminador de línea en modo binario
                if b'\r\n' in raw_data:
                    line_ending = "Windows (CRLF)"
                elif b'\n' in raw_data:
                    line_ending = "Unix (LF)"
                elif b'\r' in raw_data:
                    line_ending = "Mac (CR)"
                else:
                    line_ending = "Desconocido"

                # Leer el archivo con la codificación detectada
                with open(file_path, 'r', encoding=encoding, errors='replace') as file:
                    content = file.read()

                # Guardar codificación y terminador de línea
                self.file_encodings[file_path] = {'encoding': encoding, 'line_ending': line_ending}

                # Actualizar etiqueta de codificación
                self.encoding_label.setText(f"Codificación: {encoding} | Terminador de línea: {line_ending}")

                # Cargar el contenido en la pestaña actual o abrir una nueva
                current_widget = self.get_current_text_widget()
                if current_widget and not current_widget.toPlainText().strip():
                    current_widget.setPlainText(content)
                    index = self.tab_widget.indexOf(current_widget)
                    self.tab_widget.setTabText(index, os.path.basename(file_path))
                    self.opened_files[index] = file_path
                else:
                    self.add_new_tab(file_name=os.path.basename(file_path), content=content, file_path=file_path)

                # Guardar la última ruta en la configuración
                self.config['last_opened_path'] = os.path.dirname(file_path)
                self.save_config()  # Guardar la configuración actualizada

                # Actualizar el título de la ventana
                self.update_window_title()

                # Añadir a la lista de archivos recientes
                self.add_to_recent_files(file_path)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo: {str(e)}")
        else:
            QMessageBox.warning(self, "Error", "El archivo no es válido o no existe.")

    def new_file(self):
        current_widget = self.get_current_text_widget()
        if current_widget:
            current_widget.clear()
        self.current_file = None
        self.setWindowTitle("Lector y Editor de Texto - Nuevo archivo")

    def add_to_recent_files(self, file_path):
        from datetime import datetime

        recent_files = self.config.get('recent_files', [])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Eliminar si ya existe
        recent_files = [f for f in recent_files if f['path'] != file_path]

        # Añadir al inicio
        recent_files.insert(0, {'path': file_path, 'timestamp': timestamp})

        # Limitar a 15 archivos
        self.config['recent_files'] = recent_files[:9]
        self.save_config()
        self.update_recent_files_menu()

    def open_file(self):
        # Obtener la última ruta desde la configuración
        last_path = self.config.get('last_opened_path', '')

        # Abrir el cuadro de diálogo de selección de archivo, iniciando en la última ruta
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir archivo", last_path, "Archivos de texto (*.txt)")
        if file_path:
            try:
                # Detectar la codificación del archivo
                with open(file_path, 'rb') as file:
                    raw_data = file.read()
                    detected = chardet.detect(raw_data)
                    encoding = detected['encoding'] or 'utf-8'

                # Detectar el tipo de terminador de línea en modo binario
                if b'\r\n' in raw_data:
                    line_ending = "Windows (CRLF)"
                elif b'\n' in raw_data:
                    line_ending = "Unix (LF)"
                elif b'\r' in raw_data:
                    line_ending = "Mac (CR)"
                else:
                    line_ending = "Desconocido"

                # Leer el archivo con la codificación detectada
                with open(file_path, 'r', encoding=encoding, errors='replace') as file:
                    content = file.read()

                # Guardar la codificación y el terminador de línea
                self.file_encodings[file_path] = {'encoding': encoding, 'line_ending': line_ending}

                # Actualizar la etiqueta de codificación y terminador de línea
                self.encoding_label.setText(f"Codificación: {encoding} | Terminador de línea: {line_ending}")

                # Cargar el contenido en la pestaña actual o abrir una nueva
                current_widget = self.get_current_text_widget()
                if current_widget and not current_widget.toPlainText().strip():
                    current_widget.setPlainText(content)
                    index = self.tab_widget.indexOf(current_widget)
                    self.tab_widget.setTabText(index, os.path.basename(file_path))
                    self.opened_files[index] = file_path
                else:
                    self.add_new_tab(file_name=os.path.basename(file_path), content=content, file_path=file_path)

                # Guardar la última ruta en la configuración
                self.config['last_opened_path'] = os.path.dirname(file_path)
                self.save_config()  # Guardar la configuración actualizada

                # Actualizar el título de la ventana
                self.update_window_title()

                # Añadir a la lista de archivos recientes
                self.add_to_recent_files(file_path)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo: {str(e)}")

    def load_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                current_widget = self.get_current_text_widget()
                if current_widget:
                    current_widget.setPlainText(content)
            self.current_file = file_path
            self.setWindowTitle(f"Lector y Editor de Texto - {os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo: {str(e)}")

    def save_file(self):
        current_widget = self.get_current_text_widget()
        if not current_widget:
            QMessageBox.warning(self, "Error", "No hay ninguna pestaña activa para guardar.")
            return

        index = self.tab_widget.currentIndex()
        file_path = self.opened_files.get(index)

        if file_path:
            # Guardar directamente en la ubicación conocida con la codificación y fin de línea originales
            try:
                encoding = self.file_encodings.get(file_path, {}).get('encoding', 'utf-8')
                line_ending = self.file_encodings.get(file_path, {}).get('line_ending', 'Unix (LF)')

                # Obtener el contenido y ajustar el fin de línea
                content = current_widget.toPlainText()
                if line_ending == "Windows (CRLF)":
                    content = content.replace('\n', '\r\n')
                elif line_ending == "Mac (CR)":
                    content = content.replace('\n', '\r')

                with open(file_path, 'w', encoding=encoding) as file:
                    file.write(content)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo: {str(e)}")
        else:
            # Si no hay ubicación conocida, mostrar "Guardar como"
            self.save_file_as()

        current_widget.document().setModified(False)  # Marcar como no modificado
        self.update_window_title()  # Actualizar el título

    def save_file_as_original(self):
        current_widget = self.get_current_text_widget()
        if not current_widget:
            QMessageBox.warning(self, "Error", "No hay ninguna pestaña activa para guardar.")
            return

        # Obtener el índice de la pestaña actual y el nombre del archivo asociado
        index = self.tab_widget.currentIndex()
        suggested_name = self.opened_files.get(index, "Nuevo archivo.txt")

        # Mostrar cuadro de diálogo "Guardar como"
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar archivo", suggested_name, "Archivos de texto (*.txt)")
        if file_path:
            try:
                # Obtener la codificación y el fin de línea originales
                encoding = self.file_encodings.get(suggested_name, {}).get('encoding', 'utf-8')
                line_ending = self.file_encodings.get(suggested_name, {}).get('line_ending', 'Unix (LF)')

                # Ajustar el fin de línea en el contenido
                content = current_widget.toPlainText()
                if line_ending == "Windows (CRLF)":
                    content = content.replace('\n', '\r\n')
                elif line_ending == "Mac (CR)":
                    content = content.replace('\n', '\r')

                # Guardar el archivo
                with open(file_path, 'w', encoding=encoding) as file:
                    file.write(content)

                # Actualizar datos del archivo en la pestaña
                self.opened_files[index] = file_path
                self.file_encodings[file_path] = {'encoding': encoding, 'line_ending': line_ending}
                self.tab_widget.setTabText(index, os.path.basename(file_path))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo: {str(e)}")

    def save_file_with_encoding(self):
        current_widget = self.get_current_text_widget()
        if not current_widget:
            QMessageBox.warning(self, "Error", "No hay ninguna pestaña activa para guardar.")
            return

        # Obtener el índice de la pestaña actual y el nombre del archivo asociado
        index = self.tab_widget.currentIndex()
        suggested_name = self.opened_files.get(index, "Nuevo archivo.txt")

        # Mostrar cuadro de diálogo "Guardar como"
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar archivo", suggested_name, "Archivos de texto (*.txt)")
        if file_path:
            # Cuadro de diálogo para seleccionar codificación
            encoding, ok = QInputDialog.getItem(
                self,
                "Seleccionar codificación",
                "Codificación:",
                ["UTF-8", "UTF-16 LE", "UTF-16 BE", "UTF-8 con BOM", "ANSI", "ISO-8859-1"],
                0,
                False
            )
            if not ok:
                return

            # Cuadro de diálogo para seleccionar tipo de fin de línea
            line_ending, ok = QInputDialog.getItem(
                self,
                "Seleccionar terminador de línea",
                "Terminador de línea:",
                ["Windows (CRLF)", "Unix (LF)", "Mac (CR)"],
                0,
                False
            )
            if not ok:
                return

            try:
                # Ajustar el fin de línea en el contenido
                content = current_widget.toPlainText()
                if line_ending == "Windows (CRLF)":
                    content = content.replace('\n', '\r\n')
                elif line_ending == "Mac (CR)":
                    content = content.replace('\n', '\r')

                # Guardar con la codificación seleccionada
                if encoding == "UTF-8 con BOM":
                    with open(file_path, 'w', encoding='utf-8-sig') as file:
                        file.write(content)
                elif encoding == "ANSI":
                    with open(file_path, 'w', encoding='windows-1252') as file:
                        file.write(content)
                else:
                    with open(file_path, 'w', encoding=encoding.lower().replace(" ", "-")) as file:
                        file.write(content)

                # Actualizar datos del archivo en la pestaña
                self.opened_files[index] = file_path
                self.file_encodings[file_path] = {'encoding': encoding, 'line_ending': line_ending}
                self.tab_widget.setTabText(index, os.path.basename(file_path))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo: {str(e)}")


    def start_scrolling(self):
        if not self.is_scrolling:
            self.is_scrolling = True
            self.scroll_text()

    def pause_scrolling(self):
        self.is_scrolling = False

    def scroll_text(self):
        if self.is_scrolling:
            current_widget = self.get_current_text_widget()
            if current_widget:
                scrollbar = current_widget.verticalScrollBar()
            scrollbar.setValue(scrollbar.value() + 1)
            QTimer.singleShot(self.scroll_speed, self.scroll_text)

    def calculate_speed(self, value):
        min_speed = 1
        factor = math.log(self.max_speed / min_speed) / 29
        return max(1, int(min_speed * math.exp(factor * (30 - value))))

    def update_speed(self):
        self.scroll_speed = self.calculate_speed(self.speed_slider.value())
        # Guardar la posición del deslizador en la configuración
        self.config['last_slider_position'] = self.speed_slider.value()
        self.save_config()

    def change_max_speed(self):
        new_max_speed, ok = QInputDialog.getInt(
            self, "Cambiar velocidad máxima",
            "Ingrese la nueva velocidad máxima (1-1000):",
            value=self.max_speed, min=1, max=1000
        )
        if ok:
            self.max_speed = new_max_speed
            self.update_speed()
            self.save_config()
            QMessageBox.information(self, "Velocidad actualizada",
                                    f"La velocidad máxima se ha actualizado a {self.max_speed}.\n"
                                    f"Use el control deslizante para ajustar la velocidad entre 1 y {self.max_speed}.")

    def show_transpose_menu(self):
        transpose_menu = QMenu(self)
        for i in range(-7, 8):
            action = QAction(f"{i:+d}" if i != 0 else "0 (Original)", self)
            action.triggered.connect(lambda checked, x=i: self.transpose_chords(x))
            transpose_menu.addAction(action)
        transpose_menu.exec(self.transpose_button.mapToGlobal(self.transpose_button.rect().bottomLeft()))

    def transpose_chords(self, semitones):
        # Guardar la posición actual del scroll
        current_widget = self.get_current_text_widget()
        if current_widget:
            current_scroll_position = current_widget.verticalScrollBar().value()

        # Obtener el contenido actual y transponerlo
        current_widget = self.get_current_text_widget()
        if current_widget:
            content = current_widget.toPlainText()
        transposed_content = self.transpose_text(content, semitones)

        # Usar QTextCursor para reemplazar el texto sin perder el historial de deshacer
        current_widget = self.get_current_text_widget()
        if current_widget:
            cursor = current_widget.textCursor()
        cursor.beginEditBlock()  # Agrupa los cambios para que sean una sola acción de deshacer
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.insertText(transposed_content)
        cursor.endEditBlock()

        # Restaurar la posición del scroll
        current_widget = self.get_current_text_widget()
        if current_widget:
            current_widget.verticalScrollBar().setValue(current_scroll_position)

    def transpose_text(self, text, semitones):
        chord_pattern = r'\b[A-G](#|b)?(m|maj|min|dim|aug|sus|add)?[0-9]?(?!\w)'
        chord_base = [
            ['C'], ['C#', 'Db'], ['D'], ['D#', 'Eb'], ['E'], ['F'],
            ['F#', 'Gb'], ['G'], ['G#', 'Ab'], ['A'], ['A#', 'Bb'], ['B']
        ]

        use_sharps = self.config['use_sharps']

        def transpose_chord(chord, spaces_after):
            root = chord[0]
            accidental = '#' if '#' in chord else 'b' if 'b' in chord else ''
            suffix = chord[len(root + accidental):]

            current_index = next(i for i, group in enumerate(chord_base) if root + accidental in group)
            new_index = (current_index + semitones) % len(chord_base)

            # Elegir entre sostenidos y bemoles según la configuración
            new_root = chord_base[new_index][0] if self.config['use_sharps'] else chord_base[new_index][-1]

            # Reconstruir el acorde con la nueva raíz
            return new_root + suffix, ' ' * spaces_after

        def is_chord_line(line):
            words = line.split()
            matches = [bool(re.fullmatch(chord_pattern, word)) for word in words]
            # Considera la línea como acorde si más del 50% de las palabras coinciden con el patrón de acordes
            return sum(matches) > len(words) / 2

        def process_line(line):
            chord_positions = list(re.finditer(chord_pattern, line))
            if not chord_positions:
                return line

            new_line = []
            last_end = 0

            for i, match in enumerate(chord_positions):
                # Añadir el texto entre acordes
                new_line.append(line[last_end:match.start()])

                # Calcular espacios después del acorde
                next_pos = chord_positions[i + 1].start() if i + 1 < len(chord_positions) else len(line)
                spaces_after = next_pos - match.end()

                # Transponer el acorde
                new_chord, new_spaces = transpose_chord(match.group(), spaces_after)
                new_line.append(new_chord + new_spaces)

                last_end = next_pos

            # Añadir el resto de la línea después del último acorde
            new_line.append(line[last_end:])
            return ''.join(new_line)

        lines = text.split('\n')
        transposed_lines = [process_line(line) if is_chord_line(line) else line for line in lines]
        return '\n'.join(transposed_lines)

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'max_speed': 100,
                'font_family': 'Noto Mono',
                'font_size': 10,
                'last_opened_path': '',  # Valor predeterminado para la última ruta
                'use_sharps': True
            }

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)  # Guardar con formato legible

    def toggle_accidentals(self, use_sharps):
        # Cambiar la configuración de uso de sostenidos o bemoles
        self.config['use_sharps'] = use_sharps
        self.save_config()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TextScrollerApp()
    window.show()
    sys.exit(app.exec())
