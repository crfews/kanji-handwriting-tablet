from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import pyqtSignal

class SettingsPage(QWidget):
    navigate = pyqtSignal(str)

    def __init__(self, state: dict):
        super().__init__()
        self.state = state

        label = QLabel("Settings")
        name_edit = QLineEdit(self.state.get("username", ""))
        name_edit.setPlaceholderText("Enter username")

        save_btn = QPushButton("Save")
        back_btn = QPushButton("Back to Home")

        def save():
            self.state["username"] = name_edit.text().strip() or "guest"

        save_btn.clicked.connect(save)
        back_btn.clicked.connect(lambda: self.navigate.emit("home"))

        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(name_edit)
        layout.addWidget(save_btn)
        layout.addWidget(back_btn)
        layout.addStretch()
