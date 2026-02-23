from data import *
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QProgressBar, QLabel
from PyQt6.QtGui import QFont



class LearnCardWidget(QWidget):
    def set_card(self, card: KanaCard | KanjiCard | PhraseCard):
        pass
    
    def __init__(self, card: KanaCard | KanjiCard | PhraseCard,parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        if isinstance(card, KanaCard):
            kana_label = QLabel(f'Kana: {card.kana}')
            kana_label.setFont(QFont('Arial', 24))
            layout.addWidget(kana_label)
            
            romaji_label = QLabel(f'Romaji: {card.romaji}')
            romaji_label.setFont(QFont('Arial', 24))
            layout.addWidget(romaji_label)

            # Take a drawing and return
            
        elif isinstance(card, KanjiCard):
            kanji_label = QLabel(f'Kanji: {card.kanji}')
            layout.addWidget(kanji_label)
            if card.on_yomi:
                on_yomi_label = QLabel(f'Onyomi: {card.on_yomi}')
                on_yomi_label.setFont(QFont('Arial', 24))
                layout.addWidget(on_yomi_label)
            if card.kun_yomi:
                kun_yomi_label = QLabel(f'Kunyomi: {card.kun_yomi}')
                kun_yomi_label.setFont(QFont('Arial', 24))
                layout.addWidget(kun_yomi_label)
            pass
        elif isinstance(card, PhraseCard):
            pass
