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
        assert self.search_lineEdit is not None
        assert self.meaning_lineEdit is not None
        assert self.related_lineEdit is not None

        assert self.kana_radioButton is not None
        assert self.kanji_radioButton is not None
        assert self.phrase_radioButton is not None

        assert self.save_pushButton is not None
        assert self.delete_pushButton is not None
        assert self.search_pushButton is not None

        # Connecting response functions to UI interactions
        self.kana_radioButton.clicked.connect(self.on_kana_radio_clicked)
        self.kanji_radioButton.clicked.connect(self.on_kanji_radio_clicked)
        self.phrase_radioButton.clicked.connect(self.on_phrase_radio_clicked)

        self.search_lineEdit.editingFinished.connect(self.on_search_editing_finished)
        self.answer_lineEdit.editingFinished.connect(self.on_answer_editing_finished)
        self.kana_lineEdit.editingFinished.connect(self.on_kana_editing_finished)
        self.romaji_lineEdit.editingFinished.connect(self.on_romaji_editing_finished)
        self.related_lineEdit.editingFinished.connect(self.on_related_editing_finished)
        self.meaning_lineEdit.editingFinished.connect(self.on_meaning_editing_finished)

        self.save_pushButton.clicked.connect(self.on_save_pushbutton_clicked)
        self.delete_pushButton.clicked.connect(self.on_delete_pushbutton_clicked)
        self.search_pushButton.clicked.connect(self.on_search_pushbutton_clicked)

        # Default set the character radio button
        self.kana_radioButton.setChecked(True)
        self.on_kana_radio_clicked()

    # TODO: adjust these limits, they are arbitrarily chosen, and discuss radio button meaning
    def on_kana_radio_clicked(self) -> None:
        self.answer_lineEdit.setMaxLength(1)
        # self.kana_lineEdit.clear();
        # self.kana_lineEdit.setMaxLength(0)
        self.card_config['type'] = 0
        print('character radio clicked')

    def on_kanji_radio_clicked(self) -> None:
        self.answer_lineEdit.setMaxLength(5)
        self.card_config['type'] = 1
        print('word radio clicked')
    
    def on_phrase_radio_clicked(self) -> None:
        self.answer_lineEdit.setMaxLength(18)
        self.card_config['type'] = 2
        print('phrase radio clicked')

    # TODO: update search terms
    def on_search_editing_finished(self) -> None:
        print(f'search field now has {self.search_lineEdit.text()}')

    #TODO: update answer, kana, romaji, fields of card based on input
    def on_answer_editing_finished(self) -> None:
        self.card_config['answer'] = self.answer_lineEdit.text()
        print('answer edited')

    def on_kana_editing_finished(self) -> None:
        self.card_config['info']['kana'] = self.kana_lineEdit.text()
        print('kana edited')

    def on_romaji_editing_finished(self) -> None:
        self.card_config['info']['romaji'] = self.romaji_lineEdit.text()
        print('romaji edited')

    def on_meaning_editing_finished(self) -> None:
        self.card_config['info']['meaning'] = self.meaning_lineEdit.text()
        print('meaning edited')

    def on_related_editing_finished(self) -> None:
        self.card_config['info']['related'] = self.related_lineEdit.text()
        print('related info finished')

    def on_save_pushbutton_clicked(self) -> None:
        #TODO: add entry to database, autofill card entry fields
        print('save clicked')

    def on_delete_pushbutton_clicked(self) -> None:
        #TODO: delete entry from database
        print('delete clicked')

    def on_search_pushbutton_clicked(self) -> None:
        print('search clicked')
        #TODO: parse self.search_lineEdit.text(), conduct search on database, and populate kanji list window

