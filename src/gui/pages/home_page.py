from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import pyqtSignal, Qt

class HomePage(QWidget):
    # navigate = pyqtSignal(str)  # emit "settings" / "about" / "home"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):


        # title = QLabel(f"Home — hello, {self.state.get('username', 'guest')}!")
        # title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # btn_settings = QPushButton("Go to Settings")
        # btn_about = QPushButton("About")

        # btn_settings.clicked.connect(lambda: self.navigate.emit("settings"))
        # btn_about.clicked.connect(lambda: self.navigate.emit("about"))

        # layout = QVBoxLayout(self)
        # layout.addWidget(title)
        # layout.addWidget(btn_settings)
        # layout.addWidget(btn_about)
        # layout.addStretch()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel("Kanji Handwriting Tool")
        title.setStyleSheet("font-size: 40px; font-weight: bold; margin-bottom: 30px;")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        cards_layout_review = QHBoxLayout()
        cards_layout_learn = QHBoxLayout()


        # Create the 3 horizontal buttons for the review pages
        self.btn_review_kana = QPushButton("Review Kana")
        self.btn_review_kanji = QPushButton("Review Kanji")
        self.btn_review_phrase = QPushButton("Review Phrase")
        
        # Add horizontal buttons to their review layout
        cards_layout_review.addWidget(self.btn_review_kana)
        cards_layout_review.addWidget(self.btn_review_kanji)
        cards_layout_review.addWidget(self.btn_review_phrase)
        
        # Create widget to hold horizontal buttons
        horizontal_review_buttons_widget = QWidget()
        horizontal_review_buttons_widget.setLayout(cards_layout_review)

        # Create the 3 horizontal buttons for the learning pages
        self.btn_learn_kana = QPushButton("Learn Kana")
        self.btn_learn_kanji = QPushButton("Learn Kanji")
        self.btn_learn_phrase = QPushButton("Learn Phrase")

        # Add horizontal buttons to their learn layout
        cards_layout_learn.addWidget(self.btn_learn_kana)
        cards_layout_learn.addWidget(self.btn_learn_kanji)
        cards_layout_learn.addWidget(self.btn_learn_phrase)

        # Create widget to hold horizontal buttons
        horizontal_learn_buttons_widget = QWidget()
        horizontal_learn_buttons_widget.setLayout(cards_layout_learn)

        # Buttons - store as instance variables for connection in MainWindow
        self.btn_handwriting = QPushButton("Handwriting Manager")
        # self.btn_type = QPushButton("Cards Type Manager")
        self.btn_import = QPushButton("Import")
        

        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(horizontal_review_buttons_widget)
        layout.addWidget(horizontal_learn_buttons_widget)
        layout.addWidget(self.btn_handwriting)
        # layout.addWidget(self.btn_type)
        layout.addWidget(self.btn_import)
       

        self.setLayout(layout)
