# This Python file uses the following encoding: utf-8
import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
#from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QMainWindow, QMessageBox, QTreeWidgetItem, QApplication
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        loader = QUiLoader()
        ui_file = QFile("mainwindow.ui")
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        self.ui.pushButton.clicked.connect(self.on_pushButton_clicked)
        self.ui.treeWidget_2.itemDoubleClicked.connect(self.on_treeWidget_2_itemDoubleClicked)

    def on_pushButton_clicked(self):
        QMessageBox.information(self,"Hello","Output")

    def on_treeWidget_2_itemDoubleClicked(self, item:QTreeWidgetItem, column: int):
        if item.parent() is None:
            QMessageBox.information(self, "Now studying level", item.text(column))


if __name__ == "__main__":
    # app = QGuiApplication(sys.argv)
    # engine = QQmlApplicationEngine()
    # qml_file = Path(__file__).resolve().parent / "main.qml"
    # engine.load(qml_file)
    # if not engine.rootObjects():
    #     sys.exit(-1)
    # sys.exit(app.exec())
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
