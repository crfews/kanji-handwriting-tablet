from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QWidget, QFormLayout,  QLabel, QVBoxLayout, QPushButton, QStackedWidget, QMenuBar
from PyQt6.QtCore import QMargins, Qt
from gui.pages.handwriting_manager import HandwritingManager
from gui.pages.cards_interface import CardsInterface
from gui.pages.card_type_interface import CardTypeManager
from gui.pages.home_page import HomePage



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

        # Build the home page
        # self.home_page = self.build_home_page()
        self.home_page = HomePage(self)
        self.handwriting_page = HandwritingManager(self)
        self.cards_page = CardsInterface(self)
        self.cards_type = CardTypeManager(self)

        # Create stacked widget to hold all pages
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Add pages to stack
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.handwriting_page)
        self.stack.addWidget(self.cards_page)
        self.stack.addWidget(self.cards_type)

        # Start with home
        self.stack.setCurrentWidget(self.home_page)


        # Add pages to the menu
        self.add_page_to_menu('Handwriting Manager', lambda: HandwritingManager(self))
        self.add_page_to_menu('Cards Interface', lambda: CardsInterface(self))
        self.add_page_to_menu('Cards Type Viewer', lambda: CardTypeManager(self))


    def add_page_to_menu(self, page_name, page_lambda):
        def make_page():
            page = page_lambda()
            page.setContentsMargins(QMargins(30, 60, 30, 30))
        page_action = QAction(page_name, self)
        page_action.triggered.connect(lambda: self.setCentralWidget(page_lambda()))
        assert self.pages_menu is not None
        self.pages_menu.addAction(page_action)
    
    def build_home_page(self):
        """Builds the centered landing page UI."""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel("Kanji Learner's App")
        title.setStyleSheet("font-size: 40px; font-weight: bold; margin-bottom: 30px;")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # Buttons
        btn_handwriting = QPushButton("Handwriting Manager")
        btn_cards = QPushButton("Cards Interface")
        btn_type = QPushButton("Cards Type Manager")


        btn_handwriting.clicked.connect(lambda: self.stack.setCurrentWidget(self.handwriting_page))
        btn_cards.clicked.connect(lambda: self.stack.setCurrentWidget(self.cards_page))
        btn_type.clicked.connect(lambda: self.stack.setCurrentWidget(self.cards_type))


        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(btn_handwriting)
        layout.addWidget(btn_cards)
        layout.addWidget(btn_type)


        page.setLayout(layout)
        return page
