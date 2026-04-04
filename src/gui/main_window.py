from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QStackedWidget
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
        assert self.pages_menu is not None
        self.pages_menu.addAction(page_action)


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

        # Add the global application menubar
        self.menu_bar = self.menuBar()
        assert self.menu_bar is not None
        self.pages_menu = self.menu_bar.addMenu("&Pages")

        # Add pages
        self.home_page = HomePage(self)
        self.handwriting_page = HandwritingManager(self)
 #       self.cards_page = CardsInterface(self)
        #self.review = ReviewScheduler(self)
        #self.qna_page = QNAPage(self)
        self.import_page = ImportPage(self)
        self.learn_kana_page = LearnKanaWidget(self)
        self.learn_kanji_page = LearnKanjiWidget(self)
        self.learn_phrase_page = LearnPhrasePage(self)
        self.fill_blank_page = FillBlankPracticePage(self)
        #self.review_scheduler = ReviewScheduler(self)
        self.review_kana_page = ReviewKanaPage(self)
        self.review_kanji_page = ReviewKanjiPage(self)
        self.review_phrase_page = ReviewPhrasePage(self)


        
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.stack.addWidget(self.import_page)
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.handwriting_page)
  #      self.stack.addWidget(self.cards_page)
        #self.stack.addWidget(self.review)
        #self.stack.addWidget(self.qna_page)
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
   #     self.add_page_to_menu('Cards Interface', self.cards_page)
        #self.add_page_to_menu('Review', self.review)
        #self.add_page_to_menu('QNA', self.qna_page)
        self.add_page_to_menu('Learn Kana', self.learn_kana_page)
        self.add_page_to_menu('Learn Kanji', self.learn_kanji_page)
        self.add_page_to_menu('Learn Phrase', self.learn_phrase_page)
        self.add_page_to_menu('Complete the Sentence', self.fill_blank_page)
        #self.add_page_to_menu('Review Scheduler', self.review_scheduler)
        self.add_page_to_menu('Review Kana', self.review_kana_page)
        self.add_page_to_menu('Review Kanji', self.review_kanji_page)
        self.add_page_to_menu('Review Phrase', self.review_phrase_page)
    
