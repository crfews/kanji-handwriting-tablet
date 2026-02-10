import os
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QLineEdit, QRadioButton, QPushButton


class CardsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Load the ui
        self.answer_lineEdit: QLineEdit
        self.kana_lineEdit: QLineEdit
        self.romaji_lineEdit: QLineEdit
        self.character_radioButton: QRadioButton
        self.word_radioButton: QRadioButton
        self.phrase_radioButton: QRadioButton
        self.save_pushButton: QPushButton | None = None
        ui_file_path = os.path.abspath(__file__).replace('.py', '.ui')
        
        uic.loadUi(ui_file_path, self) # pyright: ignore[reportPrivateImportUsage]

        # Verify the ui elements were correctly named
        assert self.answer_lineEdit is not None
        assert self.kana_lineEdit is not None
        assert self.romaji_lineEdit is not None
        assert self.character_radioButton is not None
        assert self.word_radioButton is not None
        assert self.phrase_radioButton is not None
        assert self.save_pushButton is not None

        self.character_radioButton.clicked.connect(self.on_character_radio_clicked)

        # Default set the character radio button
        self.character_radioButton.setChecked(True)
        self.on_character_radio_clicked()

    def on_character_radio_clicked(self) -> None:
        self.answer_lineEdit.setMaxLength(1)
        print('character radio clicked')
        pass

