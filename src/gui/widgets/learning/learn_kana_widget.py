from PyQt6.QtCore import Qt
from PyQt6 import QtWidgets
from data import KanaCard, Drawing
from gui.widgets.writing_widgets import CharacterDrawing

class LearnKanaFront(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # --- UI ---
        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(12)

        # Top: card prompt / info
        self.kana_label = QtWidgets.QLabel("", self)
        self.kana_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        f = self.kana_label.font()
        f.setPointSize(64)
        f.setBold(True)
        self.kana_label.setFont(f)

        self.romaji_label = QtWidgets.QLabel("", self)
        self.romaji_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.status_label = QtWidgets.QLabel("", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        root.addWidget(self.kana_label)
        root.addWidget(self.romaji_label)
        root.addWidget(self.status_label)

        
class LearnKanaWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        
