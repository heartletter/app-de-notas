import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit, QPushButton, QLabel,
    QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont, QImage, QTextDocument

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
        """Inserta la imagen registrándola como recurso de Qt y escalándola adecuadamente."""
        image = QImage(file_path)
        if image.isNull():
            QMessageBox.critical(self, "Error", "No se pudo cargar el archivo de imagen.")
            return

        # Redimensionar si es muy grande para que no desborde la nota
        max_width = 500
        if image.width() > max_width:
            image = image.scaledToWidth(max_width, Qt.SmoothTransformation)

        # Crear una URL única en memoria para la imagen
        resource_url = QUrl(f"file://{file_path}")
        self.document().addResource(QTextDocument.ImageResource, resource_url, image)

        # Insertar en el cursor activo
        cursor = self.textCursor()
        cursor.insertImage(file_path)
        cursor.insertText("\n")


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

        # Campo para el Título de la nota
        self.title_input = QLineEdit()
        self.title_input.setObjectName("titleInput")
        self.title_input.setPlaceholderText("Título de la nota...")
        self.title_input.setFont(QFont("Consolas", 14, QFont.Bold))
        self.title_input.textChanged.connect(self.update_note_title)

        # Barra superior con botón para insertar imagen
        top_bar = QHBoxLayout()
        self.btn_add_image = QPushButton("Insertar una imagen")
        self.btn_add_image.setObjectName("btnSecondary")
        self.btn_add_image.clicked.connect(self.open_image_dialog)
        top_bar.addWidget(self.btn_add_image)
        top_bar.addStretch()

        # Usar la nueva clase ImageTextEdit en lugar de QTextEdit
        self.text_editor = ImageTextEdit()
        self.text_editor.setObjectName("textEditor")
        self.text_editor.setPlaceholderText("...Escribe algo o arrastra imágenes aquí")
        self.text_editor.setFont(QFont("Consolas", 11))
        self.text_editor.textChanged.connect(self.auto_save)

        # Barra de estado inferior
        status_bar = QHBoxLayout()
        self.lbl_status = QLabel("Palabras: 0 | Caracteres: 0")
        self.lbl_status.setObjectName("statusLabel")
        status_bar.addStretch()
        status_bar.addWidget(self.lbl_status)

        # Agregar elementos al layout de edición
        editor_layout.addWidget(self.title_input)
        editor_layout.addLayout(top_bar)
        editor_layout.addWidget(self.text_editor)
        editor_layout.addLayout(status_bar)

        # Ensamblar interfaz principal
        main_layout.addWidget(sidebar)
        main_layout.addWidget(editor_area)

    def open_image_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Imagen", "", "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if file_path:
            self.text_editor.insert_image_from_path(file_path)

    # ------------------ LÓGICA DE NOTAS ------------------
    def load_notes(self):
        if self.notes_file.exists():
            try:
                with open(self.notes_file, "r", encoding="utf-8") as f:
                    self.notes = json.load(f)
            except Exception:
                self.notes = {}

        if not self.notes:
            self.notes = {"1": {"title": "Nota de Bienvenida", "content": "<p>¡Bienvenido a tu aplicación de notas!</p>"}}

        self.update_notes_list()
        first_id = list(self.notes.keys())[0]
        self.current_note_id = first_id
        
        # Cargar título y contenido iniciales
        self.title_input.blockSignals(True)
        self.title_input.setText(self.notes[first_id].get("title", "Nueva Nota"))
        self.title_input.blockSignals(False)

        self.text_editor.setHtml(self.notes[first_id]["content"])

    def select_note(self, item):
        note_id = item.data(Qt.UserRole)
        self.current_note_id = note_id
        content = self.notes[note_id]["content"]
        title = self.notes[note_id].get("title", "Nueva Nota")
        
        # Actualizar título en el campo de texto superior
        self.title_input.blockSignals(True)
        self.title_input.setText(title)
        self.title_input.blockSignals(False)

        # Actualizar contenido del editor
        self.text_editor.blockSignals(True)
        self.text_editor.setHtml(content)
        self.text_editor.blockSignals(False)
        
        self.update_status_label(self.text_editor.toPlainText())

    def update_note_title(self, text):
        if not self.current_note_id or self.current_note_id not in self.notes:
            return

        new_title = text.strip() if text.strip() else "Sin título"
        self.notes[self.current_note_id]["title"] = new_title

        # Actualizar el texto en la lista lateral en tiempo real
        for i in range(self.notes_list.count()):
            item = self.notes_list.item(i)
            if item.data(Qt.UserRole) == self.current_note_id:
                item.setText(new_title)
                break

        self.save_notes_to_disk()

    def save_notes_to_disk(self):
        with open(self.notes_file, "w", encoding="utf-8") as f:
            json.dump(self.notes, f, ensure_ascii=False, indent=2)

    def update_notes_list(self):
        self.notes_list.clear()
        for note_id, note in self.notes.items():
            item = QListWidgetItem(note.get("title", "Nueva Nota"))
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
        if not self.current_note_id or self.current_note_id not in self.notes:
            return

        plain_text = self.text_editor.toPlainText()
        html_content = self.text_editor.toHtml()

        # Guardar solo el contenido HTML (el título se maneja independientemente)
        self.notes[self.current_note_id]["content"] = html_content

        self.update_status_label(plain_text)
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
                QWidget#editorArea { background-color: #271a30; }
                QLineEdit#titleInput {
                    background-color: #271a30;
                    color: #c3a0eb;
                    border: none;
                    border-bottom: 2px solid #5b4491;
                    padding: 4px;
                    font-weight: bold;
                }
                QTextEdit#textEditor {
                    background-color: #271a30;
                    color: #bd9fcf;
                    border: none;
                    selection-background-color: #5b4491;
                }
                QListWidget#notesList {
                    background-color: transparent;
                    color: #a980c2;
                    border: none;
                    font-size: 18px;
                }
                QListWidget#notesList::item {
                    padding: 8px 12px;
                    border-radius: 6px;
                    margin-bottom: 6px;
                }
                QListWidget#notesList::item:selected {
                    background-color: #b8a8e1;
                    color: #6441be;
                    font-weight: bold;
                }
                QPushButton#btnPrimary {
                    background-color: #271a30;
                    color: #c3a0eb;
                    border-radius: 6px;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton#btnPrimary:hover { background-color: #b4befe; }
                QPushButton#btnDanger {
                    background-color: #271a30;
                    color: #f38ba8;
                    border-radius: 6px;
                    padding: 6px;
                }
                QPushButton#btnDanger:hover { background-color: #271a30; color: #11111b; }
                QPushButton#btnSecondary {
                    background-color: #c3a0eb;
                    color: #271a30;
                    border-radius: 6px;
                    padding: 6px;
                    font-weight: bold;
                }
                QLabel#statusLabel { color: #bd9fcf; font-size: 12px; }
            """
        else:
            style = """
                QWidget#sidebar { background-color: #f3f4f6; border-right: 1px solid #e5e7eb; }
                QWidget#editorArea { background-color: #ffffff; }
                QLineEdit#titleInput {
                    background-color: #ffffff;
                    color: #311E4D;
                    border: none;
                    border-bottom: 2px solid #e5e7eb;
                    padding: 4px;
                    font-weight: bold;
                }
                QTextEdit#textEditor {
                    background-color: #ffffff;
                    color: #8347A8;
                    border: none;
                    selection-background-color: #e5e7eb;
                }
                QListWidget#notesList {
                    background-color: transparent;
                    color: #593D73;
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
                    color: #7a56cc;
                    font-weight: bold;
                }
                QPushButton#btnPrimary {
                    background-color: #BA5EEB;
                    color: #ffffff;
                    border-radius: 6px;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton#btnPrimary:hover { background-color: #6943ba; }
                QPushButton#btnDanger {
                    background-color: #fee2e2;
                    color: #dc2626;
                    border-radius: 6px;
                    padding: 6px;
                }
                QPushButton#btnDanger:hover { background-color: #dc2626; color: #ffffff; }
                QPushButton#btnSecondary {
                    background-color: #e5e7eb;
                    color: #5b3b75;
                    border-radius: 6px;
                    padding: 6px;
                    font-weight: bold;
                }
                QLabel#statusLabel { color: #9ca3af; font-size: 12px; }
            """
        self.setStyleSheet(style)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NotesApp()
    window.show()
    sys.exit(app.exec_())