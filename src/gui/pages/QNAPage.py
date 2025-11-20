from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QProgressBar
from gui.widgets.widget_factory import Card, CardController   # adjust import paths


class QNAPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        # Stacked widget to hold question/answer widgets
        self.stacked = QStackedWidget()

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)

        layout.addWidget(self.progress)
        layout.addWidget(self.stacked)

        # Controller
        self.controller = CardController(self.stacked, self.progress)

        # Example card
        demo_card = Card(
            card_type="character",
            prompt="日",
            answer="sun/day",
            hints=["Common kanji", "Pronounced 'ni' or 'hi'"]
        )

        self.controller.load_card(demo_card)

