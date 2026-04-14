from PyQt6.QtGui import QAction, QIcon
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


class MainWindow(QMainWindow):
    """The class acting as the root widget for the whole application"""

    def add_page_to_menu(self, page_name, page_widget):
        page_action = QAction(page_name, self)
        page_action.triggered.connect(lambda: self.stack.setCurrentWidget(page_widget))
        assert self.page_menu is not None
        self.page_menu.addAction(page_action)


    def connect_home_page_buttons(self):
        """Connect home page buttons to their respective pages"""
        self.home_page.btn_handwriting.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.handwriting_page)
        )
        # self.home_page.btn_cards.clicked.connect(
        #     lambda: self.stack.setCurrentWidget(self.cards_page)
        # )
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
        self.home_page.btn_import.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.import_page)
        )
        


    def __init__(self):
        """Constructor for the main window."""

        # Setup persistant widgets that will last for the duration of the
        # application
        super().__init__()

        self.setWindowTitle('Kanji Learner\'s App') 
        self.setStyleSheet("""
            QMainWindow {
                background-color: #eff7d3;
            }
                           """) 
        
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

        # CUSTOM MENU BAR #
        self.MenuBar = QWidget()
        self.MenuBar.setStyleSheet("""
            QWidget {
                background-color: #eff7d3;
            }
        """)
        
        MenuBarLayout = QHBoxLayout(self.MenuBar)
        MenuBarLayout.setContentsMargins(5,5,5,5)


        # PAGE LAYOUT #
        self.page_btn = QPushButton(QIcon("assests/lines.png"),"")
        
        # only image/icon is shown
        self.page_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:menu-indicator {
                image: none;
            }
                                    """)
        
        self.page_menu = QMenu()
        
        # dropdown menu design
        self.page_menu.setStyleSheet("""
            QMenu::item {
                
                color: #535a3b;
            }
            QMenu::item:selected {
                background-color: #a7b99e;
                color: #cedcc3;
            }
            QMenu {
                background-color: #cedcc3;
                border: 1px solid black;
                padding: 5px 0px;
            }
                                     """)
        #self.page_menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground,True)
        #self.page_menu.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        #self.page_menu.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        #self.page_menu.setWindowOpacity(0.99)
        
        self.page_btn.setMenu(self.page_menu)
        
        MenuBarLayout.addWidget(self.page_btn)

        MenuBarLayout.addStretch()      # seperate page button on left and settings on right

        # SETTINGS LAYOUT #
        self.settings_btn = QPushButton(QIcon("assests/settings.png"), "")
        
        # only image/icon shown
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
            }
            QPushButton::menu-indicator {
                image: none;
            }
                                    """)
        
        self.settings_menu = QMenu()
        hard_review = QAction("Harder Review", self)
        hard_review.setCheckable(True)
        
        self.settings_menu.addAction(hard_review)
        self.settings_btn.setMenu(self.settings_menu)
        
        MenuBarLayout.addWidget(self.settings_btn)

##########################################################################

        # Add pages
        self.home_page = HomePage(self)
        self.handwriting_page = HandwritingManager(self)
        # self.cards_page = CardsInterface(self)
        # self.review = ReviewScheduler(self)
        # self.qna_page = QNAPage(self)
        self.import_page = ImportPage(self)
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



        self.stack.addWidget(self.import_page)
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.handwriting_page)
  #     self.stack.addWidget(self.cards_page)
  #     self.stack.addWidget(self.review)
  #     self.stack.addWidget(self.qna_page)
        self.stack.addWidget(self.learn_kana_page)
        self.stack.addWidget(self.learn_kanji_page)
        self.stack.addWidget(self.learn_phrase_page)
        self.stack.addWidget(self.fill_blank_page)
        #self.stack.addWidget(self.review_scheduler)
        self.stack.addWidget(self.review_kana_page)
        self.stack.addWidget(self.review_kanji_page)
        self.stack.addWidget(self.review_phrase_page)
        
        # Start on home
        self.stack.setCurrentWidget(self.home_page)

        # Connect home buttons
        self.connect_home_page_buttons()
        
        # Add pages to the menu
        self.add_page_to_menu('Home', self.home_page)
        self.add_page_to_menu('Import', self.import_page)
        self.add_page_to_menu('Handwriting Manager', self.handwriting_page)
   #    self.add_page_to_menu('Cards Interface', self.cards_page)
        #self.add_page_to_menu('Review', self.review)
        #self.add_page_to_menu('QNA', self.qna_page)
        self.add_page_to_menu('Learn Kana', self.learn_kana_page)
        self.add_page_to_menu('Learn Kanji', self.learn_kanji_page)
        self.add_page_to_menu('Learn Phrase', self.learn_phrase_page)
        self.add_page_to_menu('Complete the Sentence', self.fill_blank_page)
    #   self.add_page_to_menu('Review Scheduler', self.review_scheduler)
        self.add_page_to_menu('Review Kana', self.review_kana_page)
        self.add_page_to_menu('Review Kanji', self.review_kanji_page)
        self.add_page_to_menu('Review Phrase', self.review_phrase_page)
