from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QStackedWidget
from gui.pages.handwriting_manager import HandwritingManager
from gui.pages.cards_interface import CardsInterface
from gui.pages.review_scheduler import ReviewScheduler
from gui.pages.QNAPage import QNAPage
from gui.pages.home_page import HomePage
from gui.pages.cards_browser import CardBrowserWidget


class MainWindow(QMainWindow):
    """The class acting as the root widget for the whole application"""
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

        # Start with home page
        self.setCentralWidget(HomePage(parent=self))
        
        # Add pages to the menu
        self.add_page_to_menu('Search', lambda: CardBrowserWidget(parent=self))
        self.add_page_to_menu('Home', lambda: HomePage(parent=self))
        self.add_page_to_menu('Handwriting Manager', lambda: HandwritingManager(parent=self))
        self.add_page_to_menu('Cards Interface', lambda: CardsInterface(parent=self))
        self.add_page_to_menu('Review', lambda: ReviewScheduler(parent=self))
        self.add_page_to_menu('QNA', lambda: QNAPage(parent=self))

    def add_page_to_menu(self, page_name, page_lambda):
        page_action = QAction(page_name, self)
        page_action.triggered.connect(lambda: self.setCentralWidget(page_lambda()))
        assert self.pages_menu is not None
        self.pages_menu.addAction(page_action)

    # def connect_home_page_buttons(self):
    #     """Connect home page buttons to their respective pages"""
    #     self.home_page.btn_handwriting.clicked.connect(
    #         lambda: self.stack.setCurrentWidget(self.handwriting_page)
    #     )
    #     self.home_page.btn_cards.clicked.connect(
    #         lambda: self.stack.setCurrentWidget(self.cards_page)
    #     )
    #     self.home_page.btn_type.clicked.connect(
    #         lambda: self.stack.setCurrentWidget(self.cards_type)
    #     )
    #     self.home_page.btn_review.clicked.connect(
    #         lambda: self.stack.setCurrentWidget(self.review)
    #     )
    #     self.home_page.btn_review.clicked.connect(
    #         lambda: self.stack.setCurrentWidget(self.qna)
    #     )
    
