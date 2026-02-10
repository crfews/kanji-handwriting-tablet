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
        # self.setCentralWidget(HomePage(parent=self))

        self.home_page = HomePage(self)
        self.handwriting_page = HandwritingManager(self)
        self.cards_page = CardsInterface(self)
        # self.cards_type = CardTypeManager(self)
        self.review = ReviewScheduler(self)
        self.qna = QNAPage(self)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.handwriting_page)
        self.stack.addWidget(self.cards_page)
        self.stack.addWidget(self.review)
        self.stack.addWidget(self.qna)

         # Start on home
        self.stack.setCurrentWidget(self.home_page)

        # Connect home buttons
        self.connect_home_page_buttons()
        
        # Add pages to the menu
        # self.add_page_to_menu('Search', self.C)
        self.add_page_to_menu('Home', self.home_page)
        self.add_page_to_menu('Handwriting Manager', self.handwriting_page)
        self.add_page_to_menu('Cards Interface', self.cards_page)
        self.add_page_to_menu('Review', self.review)
        self.add_page_to_menu('QNA', self.qna)

    def add_page_to_menu(self, page_name, page_widget):
        page_action = QAction(page_name, self)
        page_action.triggered.connect(lambda: self.stack.setCurrentWidget(page_widget))
        assert self.pages_menu is not None
        self.pages_menu.addAction(page_action)

    def connect_home_page_buttons(self):
        """Connect home page buttons to their respective pages"""
        self.home_page.btn_handwriting.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.handwriting_page)
        )
        self.home_page.btn_cards.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.cards_page)
        )
        self.home_page.btn_type.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.cards_type)
        )
        self.home_page.btn_review.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.review)
        )
        self.home_page.btn_qna.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.qna)
        )
    
