"""Entry point for the the application."""

#### IMPORTS ###################################################################
import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from gui.theme_manager import ThemeManager

#### PROGRAM ENTRY POINT #######################################################

if __name__ == '__main__':
    app = QApplication(sys.argv)
    tm = ThemeManager(app)
    w = MainWindow(tm)
    #w.show()
    w.showFullScreen()
    app.exec()
