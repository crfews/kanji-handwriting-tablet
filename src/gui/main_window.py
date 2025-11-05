from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import QMargins
from gui.handwriting_manager import HandwritingManager
from gui.card_window import Ui_Cards_Interface


class MainWindow(QMainWindow):
    """The class acting as the root widget for the whole application"""

    state = {}
    home_page = None
    menu_bar = None
    pages_menu = None
    pages = {}
    
    def __init__(self):
        """Constructor for the main window."""

        # Setup persistant widgets that will last for the duration of the
        # application
        super().__init__()
        self.setWindowTitle('Kanji Learner\'s App')

        # Add the global application menubar
        self.menu_bar = self.menuBar()
        self.pages_menu = self.menu_bar.addMenu("&Pages")

        # Add pages
        self.add_page_to_menu('Handwriting Manager', HandwritingManager(self))
        #self.setCentralWidget(self.pages['Handwriting Manager'])
        self.ui = Ui_Cards_Interface()
        self.ui.setupUi(self)


    def add_page_to_menu(self, page_name, page):
        page.setContentsMargins(QMargins(30, 60, 30, 30))
        if page_name in self.pages:
            pass
        self.pages[page_name] = page
        page_action = QAction(page_name, self)
        page_action.triggered.connect(
           lambda: self.setCentralWidget(page))
        self.pages_menu.addAction(page_action)
    
