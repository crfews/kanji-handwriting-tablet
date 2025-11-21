from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QMenuBar
from PyQt6.QtCore import QMargins
from gui.pages.handwriting_manager import HandwritingManager
from gui.pages.cards_interface import CardsInterface
from gui.pages.card_type_interface import CardTypeManager
from gui.pages.review_scheduler import ReviewScheduler
from gui.pages.QNAPage import QNAPage


class MainWindow(QMainWindow):
    """The class acting as the root widget for the whole application"""

    state = {}
    home_page = None
    menu_bar = None
    pages_menu = None
    
    def __init__(self):
        """Constructor for the main window."""

        # Setup persistant widgets that will last for the duration of the
        # application
        super().__init__()
        self.setWindowTitle('Kanji Learner\'s App')

        # Add the global application menubar
        self.menu_bar = self.menuBar()
        assert self.menu_bar is not None
        self.pages_menu = self.menu_bar.addMenu("&Pages")

        # Add pages
        self.add_page_to_menu('Handwriting Manager', lambda: HandwritingManager(self))
        self.add_page_to_menu('Cards Interface', lambda: CardsInterface(self))
        self.add_page_to_menu('Cards Type Viewer', lambda: CardTypeManager(self))
        self.add_page_to_menu('Review', lambda: ReviewScheduler(self))
        self.add_page_to_menu('QNA', lambda: QNAPage(self))

        


    def add_page_to_menu(self, page_name, page_lambda):
        def make_page():
            page = page_lambda()
            page.setContentsMargins(QMargins(30, 60, 30, 30))
        page_action = QAction(page_name, self)
        page_action.triggered.connect(lambda: self.setCentralWidget(page_lambda()))
        assert self.pages_menu is not None
        self.pages_menu.addAction(page_action)
    
