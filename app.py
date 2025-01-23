import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QAction, QFileDialog, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
import os
import shutil
import zipfile

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photo Manager - Python")
        self.setGeometry(100, 100, 500, 300)
        
        # Ciemny motyw (prosta metoda – ustawić styleSheet)
        self.setStyleSheet("QMainWindow { background-color: #1E1E1E; color: white; }")

        # Trzymamy ścieżki w zmiennych (lub w pliku konfiguracyjnym)
        self.photosPath = None
        self.cutPath = None

        # Menu
        mainMenu = self.menuBar()
        mainMenu.setStyleSheet("QMenuBar { background-color: #2D2D2D; color: white; }"
                               "QMenu { background-color: #2D2D2D; color: white; }")
        
        fileMenu = mainMenu.addMenu("Menu")
        
        setPhotosAction = QAction("Ustaw ścieżkę folderu ze zdjęciami", self)
        setPhotosAction.triggered.connect(self.set_photos_path)
        fileMenu.addAction(setPhotosAction)
        
        setCutAction = QAction("Ustaw ścieżkę folderu na wycięte zdjęcia", self)
        setCutAction.triggered.connect(self.set_cut_path)
        fileMenu.addAction(setCutAction)

        # Główna zawartość okna: 2 przyciski
        layout = QVBoxLayout()
        
        self.btnMove = QPushButton("Przenieś Miniaturki")
        self.btnMove.clicked.connect(self.move_miniatures)
        layout.addWidget(self.btnMove)
        
        self.btnPack = QPushButton("Spakuj")
        self.btnPack.clicked.connect(self.pack_photos)
        layout.addWidget(self.btnPack)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def set_photos_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Wybierz folder ze zdjęciami")
        if folder:
            self.photosPath = folder

    def set_cut_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Wybierz folder z wyciętymi zdjęciami")
        if folder:
            self.cutPath = folder

    def move_miniatures(self):
        if not self.photosPath or not self.cutPath:
            QMessageBox.warning(self, "Błąd", "Najpierw ustaw obie ścieżki.")
            return
        
        allegroDir = os.path.join(self.photosPath, "Allegro")
        vintedDir = os.path.join(self.photosPath, "Vinted")
        
        os.makedirs(allegroDir, exist_ok=True)
        os.makedirs(vintedDir, exist_ok=True)

        # Szukamy folderów Z (x)
        for item in os.listdir(self.photosPath):
            fullPath = os.path.join(self.photosPath, item)
            if os.path.isdir(fullPath) and item.startswith("Z (") and item.endswith(")"):
                # Kopiowanie do Allegro (z miniaturkami)
                allegroZDir = os.path.join(allegroDir, item)
                copy_directory(fullPath, allegroZDir)

                folderIndex = get_number_from_folder_name(item)
                if folderIndex > 0:
                    # przeniesienie plików "0 (x)-Photoroom"
                    pattern = f"0 ({folderIndex})-Photoroom"
                    for f in os.listdir(self.cutPath):
                        if f.startswith(pattern):
                            srcFile = os.path.join(self.cutPath, f)
                            dstFile = os.path.join(allegroZDir, f)
                            shutil.copy2(srcFile, dstFile)

                # Kopiowanie do Vinted (bez miniaturek)
                vintedZDir = os.path.join(vintedDir, item)
                copy_directory(fullPath, vintedZDir)

                # Usunięcie oryginalnego folderu
                shutil.rmtree(fullPath)

        QMessageBox.information(self, "Sukces", "Przeniesiono miniaturki do Allegro i skopiowano foldery do Vinted.")

    def pack_photos(self):
        if not self.photosPath:
            QMessageBox.warning(self, "Błąd", "Najpierw ustaw ścieżkę folderu ze zdjęciami.")
            return
        
        allegroDir = os.path.join(self.photosPath, "Allegro")
        vintedDir = os.path.join(self.photosPath, "Vinted")
        zipPath = os.path.join(self.photosPath, "Zdjęcia.zip")

        if os.path.exists(zipPath):
            os.remove(zipPath)

        with zipfile.ZipFile(zipPath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if os.path.isdir(allegroDir):
                add_folder_to_zip(zipf, allegroDir, "Allegro")
            if os.path.isdir(vintedDir):
                add_folder_to_zip(zipf, vintedDir, "Vinted")
        
        QMessageBox.information(self, "Sukces", f"Spakowano Allegro i Vinted do {zipPath}")

def copy_directory(source, dest):
    os.makedirs(dest, exist_ok=True)
    for root, dirs, files in os.walk(source):
        rel_path = os.path.relpath(root, source)
        dest_dir = os.path.join(dest, rel_path)
        os.makedirs(dest_dir, exist_ok=True)
        
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dest_dir, file)
            shutil.copy2(src_file, dst_file)

def add_folder_to_zip(zipf, folder_path, arc_prefix):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            abs_file_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_file_path, folder_path)
            zipf.write(abs_file_path, os.path.join(arc_prefix, rel_path))

def get_number_from_folder_name(name):
    # "Z (2)" -> 2
    start = name.find("(")
    end = name.find(")")
    if start != -1 and end != -1:
        number_str = name[start+1:end]
        try:
            return int(number_str)
        except:
            return -1
    return -1

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
