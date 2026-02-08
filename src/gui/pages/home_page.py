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

        cards_layout = QHBoxLayout()

        # Create the 3 horizontal buttons
        self.btn_characters = QPushButton("characters")
        self.btn_words = QPushButton("words")
        self.btn_phrases = QPushButton("phrases")
        
        # Add horizontal buttons to their layout
        cards_layout.addWidget(self.btn_characters)
        cards_layout.addWidget(self.btn_words)
        cards_layout.addWidget(self.btn_phrases)
        
        # Create widget to hold horizontal buttons
        horizontal_buttons_widget = QWidget()
        horizontal_buttons_widget.setLayout(cards_layout)

        # Buttons - store as instance variables for connection in MainWindow
        self.btn_handwriting = QPushButton("Handwriting Manager")
        self.btn_cards = QPushButton("Cards Interface")
        self.btn_type = QPushButton("Cards Type Manager")

        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(horizontal_buttons_widget)
        layout.addWidget(self.btn_handwriting)
        layout.addWidget(self.btn_cards)
        layout.addWidget(self.btn_type)

        self.setLayout(layout)
