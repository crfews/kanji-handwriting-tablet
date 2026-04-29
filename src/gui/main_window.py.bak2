from functools import partial

from PyQt6.QtGui import QAction, QIcon, QActionGroup
from PyQt6.QtWidgets import (
    QMainWindow,
    QStackedWidget,
    QWidget,
    QMenu,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
)
from PyQt6.QtCore import Qt

from gui.pages.home_page import HomePage
from gui.pages.learn_kana_page import LearnKanaWidget
from gui.pages.learn_kanji_page import LearnKanjiWidget
from gui.pages.learn_phrase_page import LearnPhrasePage
from gui.pages.fill_blank_page import FillBlankPracticePage
from gui.pages.review_kana_page import ReviewKanaPage
from gui.pages.review_kanji_page import ReviewKanjiPage
from gui.pages.review_phrase_page import ReviewPhrasePage

from gui.theme_manager import ThemeManager, THEMES


class MainWindow(QMainWindow):
    """Root widget for the whole application."""

    def __init__(self, theme_manager: ThemeManager):
        super().__init__()

        self.theme_manager = theme_manager
        self.setWindowTitle("Kanji Learner's App")

        # Stores constructed page widgets.
        self.pages = {}

        # Stores page constructors.
        # Widgets are NOT created here.
        self.page_factories = {
            "Home": HomePage,
            "Learn Kana": LearnKanaWidget,
            "Learn Kanji": LearnKanjiWidget,
            "Learn Phrase": LearnPhrasePage,
            "Complete the Sentence": FillBlankPracticePage,
            "Review Kana": ReviewKanaPage,
            "Review Kanji": ReviewKanjiPage,
            "Review Phrase": ReviewPhrasePage,
        }

        # CUSTOM MENU BAR
        self.MenuBar = QWidget()

        menu_bar_layout = QHBoxLayout(self.MenuBar)
        menu_bar_layout.setContentsMargins(5, 5, 5, 5)

        # PAGE MENU
        self.page_btn = QPushButton(QIcon("assests/lines.png"), "")

        self.page_menu = QMenu()
        self.page_btn.setMenu(self.page_menu)

        menu_bar_layout.addWidget(self.page_btn)

        menu_bar_layout.addStretch()

        # SETTINGS MENU
        self.settings_btn = QPushButton(QIcon("assests/settings.png"), "")

        self.settings_menu = QMenu()
        self.settings_btn.setMenu(self.settings_menu)

        self.setup_theme_menu()

        menu_bar_layout.addWidget(self.settings_btn)

        # STACK
        self.stack = QStackedWidget()

        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addWidget(self.MenuBar)
        main_layout.addWidget(self.stack)

        self.setCentralWidget(main_container)

        # Add menu entries, but do not create pages yet.
        for page_name in self.page_factories:
            self.add_page_to_menu(page_name)

        # Lazily create and show home.
        self.navigate_to("Home")

    def add_page_to_menu(self, page_name: str):
        page_action = QAction(page_name, self)
        page_action.triggered.connect(partial(self.navigate_to, page_name))

        assert self.page_menu is not None
        self.page_menu.addAction(page_action)

    # def navigate_to(self, page_name: str):
    #     """Create a page on first navigation, then switch to it."""

    #     if page_name not in self.page_factories:
    #         raise KeyError(f"No page factory registered for: {page_name}")

    #     if page_name not in self.pages:
    #         page_class = self.page_factories[page_name]
    #         page_widget = page_class(self)

    #         self.pages[page_name] = page_widget
    #         self.stack.addWidget(page_widget)

    #         if page_name == "Home":
    #             self.connect_home_page_buttons()

    #     self.stack.setCurrentWidget(self.pages[page_name])

    def navigate_to(self, page_name: str):
        if page_name not in self.page_factories:
            raise KeyError(f"No page factory registered for: {page_name}")

        old_page = self.stack.currentWidget()

        # Create the new page every time
        page_class = self.page_factories[page_name]
        new_page = page_class(self)

        self.stack.addWidget(new_page)
        self.stack.setCurrentWidget(new_page)

        if page_name == "Home":
            self.pages["Home"] = new_page
            self.connect_home_page_buttons()

        # Delete the old page after switching
        if old_page is not None:
            old_name = None
            for name, widget in list(self.pages.items()):
                if widget is old_page:
                    old_name = name
                    break

            if old_name is not None:
                del self.pages[old_name]

            self.stack.removeWidget(old_page)
            old_page.deleteLater()
    
    # def connect_home_page_buttons(self):
    #     """Connect home page buttons to lazily-created pages."""

    #     home_page = self.pages["Home"]

    #     home_page.btn_review_kana.clicked.connect(
    #         partial(self.navigate_to, "Review Kana")
    #     )
    #     home_page.btn_review_kanji.clicked.connect(
    #         partial(self.navigate_to, "Review Kanji")
    #     )
    #     home_page.btn_review_phrase.clicked.connect(
    #         partial(self.navigate_to, "Review Phrase")
    #     )
    #     home_page.btn_learn_kana.clicked.connect(
    #         partial(self.navigate_to, "Learn Kana")
    #     )
    #     home_page.btn_learn_kanji.clicked.connect(
    #         partial(self.navigate_to, "Learn Kanji")
    #     )
    #     home_page.btn_learn_phrase.clicked.connect(
    #         partial(self.navigate_to, "Learn Phrase")
    #     )
    #     home_page.btn_fill_blank.clicked.connect(
    #         partial(self.navigate_to, "Complete the Sentence")
    #     )

    def connect_home_page_buttons(self):
        home_page = self.stack.currentWidget()
        assert home_page
        home_page.btn_review_kana.clicked.connect(
            partial(self.navigate_to, "Review Kana")
        )
        home_page.btn_review_kanji.clicked.connect(
            partial(self.navigate_to, "Review Kanji")
        )
        home_page.btn_review_phrase.clicked.connect(
            partial(self.navigate_to, "Review Phrase")
        )
        home_page.btn_learn_kana.clicked.connect(
            partial(self.navigate_to, "Learn Kana")
        )
        home_page.btn_learn_kanji.clicked.connect(
            partial(self.navigate_to, "Learn Kanji")
        )
        home_page.btn_learn_phrase.clicked.connect(
            partial(self.navigate_to, "Learn Phrase")
        )
        home_page.btn_fill_blank.clicked.connect(
            partial(self.navigate_to, "Complete the Sentence")
        )
    
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

            assert self.theme_submenu is not None
            self.theme_submenu.addAction(action)
            self.theme_action_group.addAction(action)
            self.theme_actions[theme_name] = action

        current_theme = self.theme_manager.load_saved_theme()

        if current_theme in self.theme_actions:
            self.theme_actions[current_theme].setChecked(True)
