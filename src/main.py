"""Entry point for the the application."""

#### IMPORTS ###################################################################
import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow

#### PROGRAM ENTRY POINT #######################################################

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
