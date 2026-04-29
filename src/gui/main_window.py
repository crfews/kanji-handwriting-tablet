from PyQt6.QtGui import QAction, QIcon, QActionGroup
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QWidget, QMenu, QLabel, QHBoxLayout, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from gui.pages.handwriting_manager import HandwritingManager
#from gui.pages.cards_interface import CardsInterface
#from gui.pages.review_scheduler import ReviewScheduler
from gui.pages.QNAPage import QNAPage
from gui.pages.home_page import HomePage
#from gui.pages.cards_browser import CardBrowserWidget
from gui.pages.import_page import ImportPage
from gui.pages.learn_kana_page import LearnKanaWidget
from gui.pages.learn_kanji_page import LearnKanjiWidget
#from gui.pages.review_scheduler import ReviewScheduler
from gui.pages.review_kana_page import ReviewKanaPage
from gui.pages.review_kanji_page import ReviewKanjiPage
from gui.pages.learn_phrase_page import LearnPhrasePage
from gui.pages.review_phrase_page import ReviewPhrasePage
from gui.pages.fill_blank_page import FillBlankPracticePage
from gui.theme_manager import ThemeManager, THEMES

class MainWindow(QMainWindow):
    """The class acting as the root widget for the whole application"""

    def add_page_to_menu(self, page_name, page_widget):
        page_action = QAction(page_name, self)
        page_action.triggered.connect(lambda: self.stack.setCurrentWidget(page_widget))
        assert self.page_menu is not None
        self.page_menu.addAction(page_action)


    def connect_home_page_buttons(self):
        """Connect home page buttons to their respective pages"""
        self.home_page.btn_review_kana.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.review_kana_page)
        )
        self.home_page.btn_review_kanji.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.review_kanji_page)
        )
        self.home_page.btn_review_phrase.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.review_phrase_page)
        )
        self.home_page.btn_learn_kana.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.learn_kana_page)
        )
        self.home_page.btn_learn_kanji.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.learn_kanji_page)
        )
        self.home_page.btn_learn_phrase.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.learn_phrase_page)
        )
        self.home_page.btn_fill_blank.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.fill_blank_page)
        )
        # self.home_page.btn_import.clicked.connect(
        #     lambda: self.stack.setCurrentWidget(self.import_page)
        # )
        

    def setup_theme_menu(self):
        self.theme_submenu = self.settings_menu.addMenu("Themes")
        self.theme_action_group = QActionGroup(self)
        self.theme_action_group.setExclusive(True)

        self.theme_actions = {}

        for theme_name in THEMES.keys():
            action = QAction(theme_name.replace("_", " ").title(), self)
            action.setCheckable(True)
            action.triggered.connect(
                lambda checked, name=theme_name: self.theme_manager.apply_theme(name)
            )
            assert self.theme_submenu
            self.theme_submenu.addAction(action)
            self.theme_action_group.addAction(action)
            self.theme_actions[theme_name] = action

        current_theme = self.theme_manager.load_saved_theme()
        if current_theme in self.theme_actions:
            self.theme_actions[current_theme].setChecked(True)
        
    def __init__(self, theme_manager: ThemeManager ):
        """Constructor for the main window."""

        # Setup persistant widgets that will last for the duration of the
        # application
        super().__init__()

        self.theme_manager = theme_manager
        
        self.setWindowTitle('Kanji Learner\'s App') 

        # CUSTOM MENU BAR #
        self.MenuBar = QWidget()
        
        MenuBarLayout = QHBoxLayout(self.MenuBar)
        MenuBarLayout.setContentsMargins(5,5,5,5)


        # PAGE LAYOUT #
        self.page_btn = QPushButton(QIcon("assests/lines.png"),"")
        
        self.page_menu = QMenu()
        
        self.page_btn.setMenu(self.page_menu)
        
        MenuBarLayout.addWidget(self.page_btn)

        MenuBarLayout.addStretch()      # seperate page button on left and settings on right

        # # SETTINGS LAYOUT #
        self.settings_btn = QPushButton(QIcon("assests/settings.png"), "")
        
        self.settings_menu = QMenu()
        #hard_review = QAction("Harder Review", self)
        #hard_review.setCheckable(True)
        
        #self.settings_menu.addAction(hard_review)
        self.settings_btn.setMenu(self.settings_menu)

        self.setup_theme_menu()
        
        MenuBarLayout.addWidget(self.settings_btn)

##########################################################################

        # Add pages
        self.home_page = HomePage(self)
        #self.handwriting_page = HandwritingManager(self)
        # self.cards_page = CardsInterface(self)
        # self.review = ReviewScheduler(self)
        # self.qna_page = QNAPage(self)
        #self.import_page = ImportPage(self)
        self.learn_kana_page = LearnKanaWidget(self)
        self.learn_kanji_page = LearnKanjiWidget(self)
        self.learn_phrase_page = LearnPhrasePage(self)
        self.fill_blank_page = FillBlankPracticePage(self)
        # self.review_scheduler = ReviewScheduler(self)
        self.review_kana_page = ReviewKanaPage(self)
        self.review_kanji_page = ReviewKanjiPage(self)
        self.review_phrase_page = ReviewPhrasePage(self)


        
        self.stack = QStackedWidget()
    
        #self.setCentralWidget(self.stack)
        
        main_container = QWidget()

        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addWidget(self.MenuBar)
        main_layout.addWidget(self.stack)

        self.setCentralWidget(main_container)



        # self.stack.addWidget(self.import_page)
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.learn_kana_page)
        self.stack.addWidget(self.learn_kanji_page)
        self.stack.addWidget(self.learn_phrase_page)
        self.stack.addWidget(self.fill_blank_page)
        self.stack.addWidget(self.review_kana_page)
        self.stack.addWidget(self.review_kanji_page)
        
        # Start on home
        self.stack.setCurrentWidget(self.home_page)

        # Connect home buttons
        self.connect_home_page_buttons()
        
        # Add pages to the menu
        self.add_page_to_menu('Home', self.home_page)
        self.add_page_to_menu('Learn Kana', self.learn_kana_page)
        self.add_page_to_menu('Learn Kanji', self.learn_kanji_page)
        self.add_page_to_menu('Learn Phrase', self.learn_phrase_page)
        self.add_page_to_menu('Complete the Sentence', self.fill_blank_page)
        self.add_page_to_menu('Review Kana', self.review_kana_page)
        self.add_page_to_menu('Review Kanji', self.review_kanji_page)
        self.add_page_to_menu('Review Phrase', self.review_phrase_page)

















        
        # Add the global application menubar
        #self.menu_bar = self.menuBar()
        #assert self.menu_bar is not None
        #self.menu_bar.setStyleSheet("""
        #    QMenuBar {
        #        background-color: #eff7d3;
        #    }
        #""")
        #self.pages_menu = self.menu_bar.addMenu("&Pages")
        
        #self.pages_menu.setStyleSheet("""
        #    QMenuBar:item {
        #        background-color: #eff7d3;
        #    }
        #    QMenu {
        #        background-color: #cedcc3;
        #    }
        #                              """)  
##########################################################
