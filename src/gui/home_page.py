from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt

class HomePage(QWidget):
    navigate = pyqtSignal(str)  # emit "settings" / "about" / "home"

    def __init__(self, state: dict):
        super().__init__()
        self.state = state

        title = QLabel(f"Home — hello, {self.state.get('username', 'guest')}!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_settings = QPushButton("Go to Settings")
        btn_about = QPushButton("About")

        btn_settings.clicked.connect(lambda: self.navigate.emit("settings"))
        btn_about.clicked.connect(lambda: self.navigate.emit("about"))

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(btn_settings)
        layout.addWidget(btn_about)
        layout.addStretch()
