import os
from PyQt6 import uic
from PyQt6.QtWidgets import QWidget, QLineEdit, QRadioButton, QPushButton


class CardsInterface(QWidget):

    answer_lineEdit: QLineEdit = None
    kana_lineEdit: QLineEdit = None
    romaji_lineEdit: QLineEdit = None

    character_radioButton: QRadioButton = None
    word_radioButton: QRadioButton = None
    phrase_radioButton: QRadioButton = None

    save_pushButton: QPushButton = None
    
    def __init__(self, parent=None):
        super().__init__(parent)

        # Load the ui
        ui_file_path = os.path.abspath(__file__).replace('.py', '.ui')
        uic.loadUi(ui_file_path, self)

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

