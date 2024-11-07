import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QProgressBar, QScrollArea,
                             QLineEdit, QMessageBox, QFrame, QDialog)
from PyQt6.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent, QIcon, QPainter, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PIL import Image
import subprocess

class ConversionThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, source_files, target_directory, target_width, target_height):
        super().__init__()
        self.source_files = source_files
        self.target_directory = target_directory
        self.target_width = target_width
        self.target_height = target_height

    def run(self):
        total_files = len(self.source_files)
        for i, file in enumerate(self.source_files):
            try:
                with Image.open(file) as img:
                    img_width, img_height = img.size
                    aspect_ratio = img_width / img_height
                    target_ratio = self.target_width / self.target_height

                    if aspect_ratio > target_ratio:
                        new_width = int(img_height * target_ratio)
                        offset = (img_width - new_width) // 2
                        crop_box = (offset, 0, offset + new_width, img_height)
                    else:
                        new_height = int(img_width / target_ratio)
                        offset = (img_height - new_height) // 2
                        crop_box = (0, offset, img_width, offset + new_height)

                    img_cropped = img.crop(crop_box)
                    img_resized = img_cropped.resize((self.target_width, self.target_height), Image.LANCZOS)

                    base_name = os.path.splitext(os.path.basename(file))[0]
                    output_file = os.path.join(self.target_directory, f"{base_name}_converted.png")
                    img_resized.save(output_file, "PNG")
                
                progress = int((i + 1) / total_files * 100)
                self.progress.emit(progress)
                self.status.emit(f"Verwerkt: {i+1}/{total_files}")

            except Exception as e:
                self.status.emit(f"Fout bij het converteren van {file}: {str(e)}")

        self.finished.emit()

class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bezig met converteren...")
        self.setModal(True)
        self.setFixedSize(200, 100)

        layout = QVBoxLayout(self)
        self.label = QLabel("Bezig met converteren...")
        layout.addWidget(self.label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(self.progress_bar)

class PhotoConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Foto Converter")
        self.setGeometry(100, 100, 1000, 700)

        self.source_files = []
        self.target_directory = ""

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left side (drop zone and thumbnails)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Drop zone
        self.drop_zone = QLabel()
        self.drop_zone.setFixedSize(830, 200)
        self.drop_zone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_zone.setStyleSheet("""
            background-color: transparent;
            border: 2px dashed #1E1E1E;
            border-radius: 10px;
        """)
        self.drop_zone.setAcceptDrops(True)
        self.drop_zone.dragEnterEvent = self.dragEnterEvent
        self.drop_zone.dropEvent = self.dropEvent

        # Icoon voor de drop zone
        drop_icon = QIcon.fromTheme("document-open")
        pixmap = drop_icon.pixmap(QSize(32, 32))
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor("#1E1E1E"))
        painter.end()
        
        self.drop_zone.setPixmap(pixmap)
        left_layout.addWidget(self.drop_zone)

        # Foto informatie veld
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: 2px solid #1E1E1E;
                border-radius: 10px;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #F0F0F0;
                width: 10px;
                margin: 0px 0 0px 0;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #1E1E1E;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                border: none;
                width: 0px;
                height: 0px;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        self.thumbnails_widget = QWidget()
        self.thumbnails_layout = QVBoxLayout(self.thumbnails_widget)
        self.thumbnails_layout.setSpacing(5)
        self.thumbnails_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_area.setWidget(self.thumbnails_widget)
        left_layout.addWidget(self.scroll_area)

        main_layout.addWidget(left_widget, 2)

        # Right side (controls)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.select_files_btn = QPushButton("Selecteer Bestanden")
        self.select_files_btn.clicked.connect(self.select_files)
        right_layout.addWidget(self.select_files_btn)

        self.select_dir_btn = QPushButton("Selecteer Doelmap")
        self.select_dir_btn.clicked.connect(self.select_directory)
        right_layout.addWidget(self.select_dir_btn)

        self.dir_label = QLabel("Geen map geselecteerd")
        self.dir_label.setWordWrap(True)
        right_layout.addWidget(self.dir_label)

        size_layout = QHBoxLayout()
        self.width_input = QLineEdit()
        self.width_input.setPlaceholderText("Breedte")
        self.height_input = QLineEdit()
        self.height_input.setPlaceholderText("Hoogte")
        size_layout.addWidget(self.width_input)
        size_layout.addWidget(self.height_input)
        right_layout.addLayout(size_layout)

        self.convert_btn = QPushButton("Converteer Foto's")
        self.convert_btn.clicked.connect(self.start_conversion)
        right_layout.addWidget(self.convert_btn)

        # Voeg de voortgangsbalk en percentage label toe
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(20)  # Maak de voortgangsbalk dikker
        self.progress_bar.setTextVisible(False)  # Verberg de standaard tekst
        progress_layout.addWidget(self.progress_bar)

        self.progress_percentage = QLabel("0%")
        progress_layout.addWidget(self.progress_percentage)

        right_layout.addLayout(progress_layout)

        self.status_label = QLabel("")
        right_layout.addWidget(self.status_label)

        right_layout.addStretch(1)

        main_layout.addWidget(right_widget, 1)

        # Apply some styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #1E1E1E;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QLabel {
                font-size: 14px;
                color: #1E1E1E;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #1E1E1E;
                border-radius: 3px;
                background-color: transparent;
                color: #1E1E1E;
            }
            QLineEdit::placeholder {
                color: #1E1E1E;
            }
        """)

        # Voeg extra styling toe voor de voortgangsbalk
        self.setStyleSheet(self.styleSheet() + """
            QProgressBar {
                border: 2px solid #1E1E1E;
                border-radius: 5px;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #1E1E1E;
                width: 10px;
                margin: 0.5px;
            }
        """)

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Selecteer Bestanden", "", "Image files (*.jpg *.jpeg *.png)")
        self.add_files(files)

    def add_files(self, files):
        for file in files:
            if file not in self.source_files:
                self.source_files.append(file)
                self.add_thumbnail(file)

    def add_thumbnail(self, file):
        thumbnail_widget = QWidget()
        thumbnail_layout = QHBoxLayout(thumbnail_widget)

        img = QImage(file)
        pixmap = QPixmap.fromImage(img).scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio)
        thumbnail_label = QLabel()
        thumbnail_label.setPixmap(pixmap)
        thumbnail_layout.addWidget(thumbnail_label)

        file_name = os.path.basename(file)
        name_label = QLabel(file_name)
        name_label.setStyleSheet("color: #1E1E1E;")
        thumbnail_layout.addWidget(name_label, 1)

        remove_btn = QPushButton("X")
        remove_btn.setStyleSheet("background-color: #ff4d4d; max-width: 30px;")
        remove_btn.clicked.connect(lambda _, f=file: self.on_remove_button_clicked(f))  # Verander hier de connectie
        thumbnail_layout.addWidget(remove_btn)

        self.thumbnails_layout.addWidget(thumbnail_widget)

    def on_remove_button_clicked(self, file):
        print(f"Verwijderknop ingedrukt voor: {file}")  # Debugging-uitvoer
        self.remove_file(file)

    def remove_file(self, file):
        print(f"Probeer bestand te verwijderen: {file}")  # Debugging-uitvoer
        print(f"Huidige source_files: {self.source_files}")  # Debugging-uitvoer

        if file in self.source_files:  # Controleer of het bestand in de lijst staat
            self.source_files.remove(file)
            print(f"Bestand verwijderd: {file}")  # Debugging-uitvoer

            # Verwijder de thumbnail widget
            for i in reversed(range(self.thumbnails_layout.count())): 
                widget = self.thumbnails_layout.itemAt(i).widget()
                # Controleer of de naam overeenkomt
                name_label = widget.findChildren(QLabel)[1]  # Neem de juiste QLabel
                if name_label.text() == os.path.basename(file):  # Vergelijk met de bestandsnaam
                    widget.setParent(None)  # Verwijder de widget uit de lay-out
                    print(f"Thumbnail verwijderd voor: {file}")  # Debugging-uitvoer
                    break
        else:
            print(f"Bestand niet gevonden in source_files: {file}")  # Debugging-uitvoer

    def select_directory(self):
        self.target_directory = QFileDialog.getExistingDirectory(self, "Selecteer Doelmap")
        if self.target_directory:
            self.dir_label.setText(f"Doelmap: {self.target_directory}")
        else:
            self.dir_label.setText("Geen map geselecteerd")

    def start_conversion(self):
        if not self.source_files:
            QMessageBox.warning(self, "Geen bestanden", "Selecteer eerst enkele foto's om te converteren.")
            return

        if not self.target_directory:
            QMessageBox.warning(self, "Geen doelmap", "Selecteer eerst een doelmap.")
            return

        try:
            target_width = int(self.width_input.text())
            target_height = int(self.height_input.text())
        except ValueError:
            QMessageBox.warning(self, "Ongeldige afmetingen", "Voer geldige getallen in voor breedte en hoogte.")
            return

        self.convert_btn.setEnabled(False)
        self.select_files_btn.setEnabled(False)
        self.select_dir_btn.setEnabled(False)

        self.loading_dialog = LoadingDialog(self)
        self.loading_dialog.show()

        self.conversion_thread = ConversionThread(self.source_files, self.target_directory, target_width, target_height)
        self.conversion_thread.progress.connect(self.update_progress)
        self.conversion_thread.status.connect(self.update_status)
        self.conversion_thread.finished.connect(self.conversion_finished)
        self.conversion_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        self.progress_percentage.setText(f"{value}%")

    def update_status(self, message):
        self.status_label.setText(message)

    def conversion_finished(self):
        self.loading_dialog.close()
        self.convert_btn.setEnabled(True)
        self.select_files_btn.setEnabled(True)
        self.select_dir_btn.setEnabled(True)
        self.status_label.setText("Conversie voltooid!")
        self.show_completion_message()

    def show_completion_message(self):
        total_files = len(self.source_files)
        width = self.width_input.text()
        height = self.height_input.text()
        
        message = f"Alle {total_files} foto's zijn geconverteerd naar PNG en bijgesneden naar {width}x{height}.\n"
        message += "De geüploade foto's zijn automatisch verwijderd. U kunt nu nieuwe foto's uploaden."
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Conversie Voltooid")
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        open_folder_button = msg_box.addButton("Open Doelmap", QMessageBox.ButtonRole.ActionRole)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == open_folder_button:
            self.open_output_folder()
        
        self.remove_all_files()

    def open_output_folder(self):
        if sys.platform == 'win32':
            os.startfile(self.target_directory)
        elif sys.platform == 'darwin':  # macOS
            subprocess.call(['open', self.target_directory])
        else:  # Linux
            subprocess.call(['xdg-open', self.target_directory])

    def remove_all_files(self):
        self.source_files.clear()
        for i in reversed(range(self.thumbnails_layout.count())): 
            self.thumbnails_layout.itemAt(i).widget().setParent(None)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile().lower().endswith(('.jpg', '.jpeg', '.png'))]
        self.add_files(files)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    converter = PhotoConverterApp()
    converter.show()
    sys.exit(app.exec())
