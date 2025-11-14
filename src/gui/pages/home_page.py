from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt

class HomePage(QWidget):
    navigate = pyqtSignal(str)  # emit "settings" / "about" / "home"

    def __init__(self, state: dict):
        super().__init__()
        # self.state = state

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
