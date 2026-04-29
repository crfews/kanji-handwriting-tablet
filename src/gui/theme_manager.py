from __future__ import annotations

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication
import getpass

THEMES = {
    "light": {
        "palette": {
            "window": "#f6f6f6",
            "window_text": "#111111",
            "base": "#ffffff",
            "alternate_base": "#eeeeee",
            "text": "#111111",
            "button": "#eaeaea",
            "button_text": "#111111",
            "highlight": "#4a90e2",
            "highlighted_text": "#ffffff",
        },
        "stylesheet": """
            QWidget {
                font-size: 24px;
            }
            QPushButton {
                border: 1px solid #999;
                border-radius: 6px;
                padding: 6px 10px;
                background: #eaeaea;
            }
            QPushButton:hover {
                background: #dddddd;
            }
            QLineEdit {
                border: 1px solid #aaa;
                border-radius: 4px;
                padding: 4px;
                background: #ffffff;
            }
        """
    },
    "dark": {
        "palette": {
            "window": "#2b2b2b",
            "window_text": "#f0f0f0",
            "base": "#1e1e1e",
            "alternate_base": "#2a2a2a",
            "text": "#f0f0f0",
            "button": "#3a3a3a",
            "button_text": "#f0f0f0",
            "highlight": "#3d7eff",
            "highlighted_text": "#ffffff",
        },
        "stylesheet": """
            QWidget {
                font-size: 24px;
            }
            QPushButton {
                border: 1px solid #666;
                border-radius: 6px;
                padding: 6px 10px;
                background: #3a3a3a;
                color: #f0f0f0;
            }
            QPushButton:hover {
                background: #4a4a4a;
            }
            QLineEdit {
                border: 1px solid #666;
                border-radius: 4px;
                padding: 4px;
                background: #1e1e1e;
                color: #f0f0f0;
            }
        """
    }
}


class ThemeManager:
    def __init__(self, app: QApplication) -> None:
        self.app = app
        self.settings = QSettings(getpass.getuser(), "JapaneseLearningApp")

    def apply_theme(self, theme_name: str) -> None:
        theme = THEMES[theme_name]

        palette = QPalette()
        p = theme["palette"]

        palette.setColor(QPalette.ColorRole.Window, QColor(p["window"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(p["window_text"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(p["base"]))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(p["alternate_base"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(p["text"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(p["button"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(p["button_text"]))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(p["highlight"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(p["highlighted_text"]))

        self.app.setPalette(palette)
        self.app.setStyleSheet(theme["stylesheet"])
        self.settings.setValue("theme", theme_name)

    def load_saved_theme(self) -> str:
        theme_name = self.settings.value("theme", "light")
        if not isinstance(theme_name, str) or theme_name not in THEMES:
            theme_name = "light"
        self.apply_theme(theme_name)
        return theme_name
