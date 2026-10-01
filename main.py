import sys
import json
from pathlib import Path
import base64
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QTextEdit, QPushButton, QLabel,
    QMessageBox, QFileDialog, 
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class ImageTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                    self.insert_image_from_path(file_path)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def insert_image_from_path(self, file_path):
        try:
            with open(file_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            
            ext = Path(file_path).suffix.lower().replace('.', '')
            if ext == 'jpg':
                ext = 'jpeg'

            image_format = f"data:image/{ext};base64,{encoded_string}"
            html_img = f'<br><img src="{image_format}" width="400"/><br>'
            
            cursor = self.textCursor()
            cursor.insertHtml(html_img)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la imagen: {str(e)}")



        # --- REEMPLAZAR EL ÁREA DE EDICIÓN EN init_ui CON ESTO ---
        top_bar = QHBoxLayout()
        self.btn_add_image = QPushButton("Insertar una imagen")
        self.btn_add_image.setObjectName("btnSecondary")
        self.btn_add_image.clicked.connect(self.open_image_dialog)
        top_bar.addWidget(self.btn_add_image)
        top_bar.addStretch()

        # Usar la nueva clase ImageTextEdit en lugar de QTextEdit
        self.text_editor = ImageTextEdit()
        self.text_editor.setObjectName("textEditor")
        self.text_editor.setPlaceholderText("Escribe tu nota aquí o arrastra imágenes!")
        self.text_editor.setFont(QFont("Consolas", 11))
        self.text_editor.textChanged.connect(self.auto_save)

        # Barra de estado inferior
        status_bar = QHBoxLayout()
        self.lbl_status = QLabel("Palabras: 0 | Caracteres: 0")
        self.lbl_status.setObjectName("statusLabel")
        status_bar.addStretch()
        status_bar.addWidget(self.lbl_status)

        editor_layout.addLayout(top_bar) # <--- Añadir esta línea
        editor_layout.addWidget(self.text_editor)
        editor_layout.addLayout(status_bar)


    def open_image_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Imagen", "", "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if file_path:
            self.text_editor.insert_image_from_path(file_path)


    # En load_notes():
    # Cambia self.text_editor.setText(...) por:
    self.text_editor.setHtml(self.notes[first_id]["content"])

    # En select_note():
    # Cambia self.text_editor.setText(...) por:
    self.text_editor.setHtml(content)

    # En auto_save():
    # Guarda el HTML en lugar del texto plano para preservar las imágenes:
    def auto_save(self):
        if not self.current_note_id:
            return

        plain_text = self.text_editor.toPlainText()
        html_content = self.text_editor.toHtml()

        lines = [line for line in plain_text.strip().split("\n") if line.strip()]
        title = lines[0][:25] if lines else "Nota con Imagen"

        self.notes[self.current_note_id]["content"] = html_content
        self.notes[self.current_note_id]["title"] = title

        for i in range(self.notes_list.count()):
            item = self.notes_list.item(i)
            if item.data(Qt.UserRole) == self.current_note_id:
                item.setText(title)
                break

        self.update_status_label(plain_text)
        self.save_notes_to_disk()

class NotesApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.notes_file = Path("notas_data.json")
        self.notes = {}
        self.current_note_id = None
        
        self.init_ui()
        self.load_notes()
        self.apply_theme(dark=True)

    def init_ui(self):
        self.setWindowTitle("Stick notes")
        self.resize(900, 600)

        # Contenedor principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ------------------ BARRA LATERAL ------------------
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)

        # Botones superiores
        self.btn_new = QPushButton("+ Nueva Nota")
        self.btn_new.setObjectName("btnPrimary")
        self.btn_new.clicked.connect(self.add_note)

        self.btn_delete = QPushButton("Eliminar")
        self.btn_delete.setObjectName("btnDanger")
        self.btn_delete.clicked.connect(self.delete_note)

        # Lista de notas
        self.notes_list = QListWidget()
        self.notes_list.setObjectName("notesList")
        self.notes_list.itemClicked.connect(self.select_note)

        # Botón de Tema
        self.btn_theme = QPushButton("Modo Claro")
        self.btn_theme.setObjectName("btnSecondary")
        self.btn_theme.setCheckable(True)
        self.btn_theme.toggled.connect(self.toggle_theme)

        sidebar_layout.addWidget(self.btn_new)
        sidebar_layout.addWidget(self.notes_list)
        sidebar_layout.addWidget(self.btn_delete)
        sidebar_layout.addWidget(self.btn_theme)
        sidebar.setFixedWidth(240)

        # ------------------ ÁREA DE EDICIÓN ------------------
        editor_area = QWidget()
        editor_area.setObjectName("editorArea")
        editor_layout = QVBoxLayout(editor_area)
        editor_layout.setContentsMargins(20, 20, 20, 20)

        # Editor de texto
        self.text_editor = QTextEdit()
        self.text_editor.setObjectName("textEditor")
        self.text_editor.setPlaceholderText("...Escribe algo")
        self.text_editor.setFont(QFont("Consolas", 11))
        self.text_editor.textChanged.connect(self.auto_save)

        # Barra de estado inferior
        status_bar = QHBoxLayout()
        self.lbl_status = QLabel("Palabras: 0 | Caracteres: 0")
        self.lbl_status.setObjectName("statusLabel")
        status_bar.addStretch()
        status_bar.addWidget(self.lbl_status)

        editor_layout.addWidget(self.text_editor)
        editor_layout.addLayout(status_bar)

        # Ensamblar interfaz
        main_layout.addWidget(sidebar)
        main_layout.addWidget(editor_area)

    # ------------------ LÓGICA DE NOTAS ------------------
    def load_notes(self):
        if self.notes_file.exists():
            try:
                with open(self.notes_file, "r", encoding="utf-8") as f:
                    self.notes = json.load(f)
            except Exception:
                self.notes = {}

        if not self.notes:
            self.notes = {"1": {"title": "Nota de Bienvenida", "content": "¡Comienza a anotar!"}}

        self.update_notes_list()
        # Seleccionar la primera nota
        first_id = list(self.notes.keys())[0]
        self.current_note_id = first_id
        self.text_editor.setText(self.notes[first_id]["content"])

    def save_notes_to_disk(self):
        with open(self.notes_file, "w", encoding="utf-8") as f:
            json.dump(self.notes, f, ensure_ascii=False, indent=2)

    def update_notes_list(self):
        self.notes_list.clear()
        for note_id, note in self.notes.items():
            item = QListWidgetItem(note["title"])
            item.setData(Qt.UserRole, note_id)
            self.notes_list.addItem(item)

    def add_note(self):
        new_id = str(len(self.notes) + 1)
        count = 1
        while new_id in self.notes:
            new_id = str(len(self.notes) + 1 + count)
            count += 1

        self.notes[new_id] = {"title": "Nueva Nota", "content": ""}
        self.save_notes_to_disk()
        self.update_notes_list()

        # Seleccionar la nota recién creada
        for i in range(self.notes_list.count()):
            item = self.notes_list.item(i)
            if item.data(Qt.UserRole) == new_id:
                self.notes_list.setCurrentItem(item)
                self.select_note(item)
                break

    def select_note(self, item):
        note_id = item.data(Qt.UserRole)
        self.current_note_id = note_id
        content = self.notes[note_id]["content"]
        
        # Evitar loop infinito con textChanged
        self.text_editor.blockSignals(True)
        self.text_editor.setText(content)
        self.text_editor.blockSignals(False)
        
        self.update_status_label(content)

    def delete_note(self):
        if not self.current_note_id or len(self.notes) <= 1:
            QMessageBox.warning(self, "Aviso", "No puedes eliminar la única nota existente.")
            return

        confirm = QMessageBox.question(
            self, "Confirmar eliminación",
            "¿Estás seguro de que deseas eliminar esta nota?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            del self.notes[self.current_note_id]
            self.save_notes_to_disk()
            self.load_notes()

    def auto_save(self):
        if not self.current_note_id:
            return

        text = self.text_editor.toPlainText()
        lines = text.strip().split("\n")
        title = lines[0][:25] if lines and lines[0] else "Sin título"

        self.notes[self.current_note_id]["content"] = text
        self.notes[self.current_note_id]["title"] = title

        # Actualizar título en la lista lateral
        for i in range(self.notes_list.count()):
            item = self.notes_list.item(i)
            if item.data(Qt.UserRole) == self.current_note_id:
                item.setText(title)
                break

        self.update_status_label(text)
        self.save_notes_to_disk()

    def update_status_label(self, text):
        words = len(text.split()) if text else 0
        chars = len(text)
        self.lbl_status.setText(f"Palabras: {words} | Caracteres: {chars}")

    # ------------------ ESTILOS Y TEMA ------------------
    def toggle_theme(self, checked):
        if checked:
            self.btn_theme.setText("Modo Oscuro")
            self.apply_theme(dark=False)
        else:
            self.btn_theme.setText("Modo Claro")
            self.apply_theme(dark=True)

    def apply_theme(self, dark=True):
        if dark:
            style = """
                QWidget#sidebar { background-color: #1e1e2e; border-right: 1px solid #313244; }
                QWidget#editorArea { background-color: #181825; }
                QTextEdit#textEditor {
                    background-color: #181825;
                    color: #cdd6f4;
                    border: none;
                    selection-background-color: #45475a;
                }
                QListWidget#notesList {
                    background-color: transparent;
                    color: #cdd6f4;
                    border: none;
                    font-size: 14px;
                }
                QListWidget#notesList::item {
                    padding: 8px 12px;
                    border-radius: 6px;
                    margin-bottom: 4px;
                }
                QListWidget#notesList::item:selected {
                    background-color: #313244;
                    color: #89b4fa;
                    font-weight: bold;
                }
                QPushButton#btnPrimary {
                    background-color: #89b4fa;
                    color: #11111b;
                    border-radius: 6px;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton#btnPrimary:hover { background-color: #b4befe; }
                QPushButton#btnDanger {
                    background-color: #313244;
                    color: #f38ba8;
                    border-radius: 6px;
                    padding: 6px;
                }
                QPushButton#btnDanger:hover { background-color: #f38ba8; color: #11111b; }
                QPushButton#btnSecondary {
                    background-color: #313244;
                    color: #cdd6f4;
                    border-radius: 6px;
                    padding: 6px;
                }
                QLabel#statusLabel { color: #6c7086; font-size: 12px; }
            """
        else:
            style = """
                QWidget#sidebar { background-color: #f3f4f6; border-right: 1px solid #e5e7eb; }
                QWidget#editorArea { background-color: #ffffff; }
                QTextEdit#textEditor {
                    background-color: #ffffff;
                    color: #1f2937;
                    border: none;
                    selection-background-color: #e5e7eb;
                }
                QListWidget#notesList {
                    background-color: transparent;
                    color: #374151;
                    border: none;
                    font-size: 14px;
                }
                QListWidget#notesList::item {
                    padding: 8px 12px;
                    border-radius: 6px;
                    margin-bottom: 4px;
                }
                QListWidget#notesList::item:selected {
                    background-color: #e5e7eb;
                    color: #2563eb;
                    font-weight: bold;
                }
                QPushButton#btnPrimary {
                    background-color: #2563eb;
                    color: #ffffff;
                    border-radius: 6px;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton#btnPrimary:hover { background-color: #1d4ed8; }
                QPushButton#btnDanger {
                    background-color: #fee2e2;
                    color: #dc2626;
                    border-radius: 6px;
                    padding: 6px;
                }
                QPushButton#btnDanger:hover { background-color: #dc2626; color: #ffffff; }
                QPushButton#btnSecondary {
                    background-color: #e5e7eb;
                    color: #374151;
                    border-radius: 6px;
                    padding: 6px;
                }
                QLabel#statusLabel { color: #9ca3af; font-size: 12px; }
            """
        self.setStyleSheet(style)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NotesApp()
    window.show()
    sys.exit(app.exec_())