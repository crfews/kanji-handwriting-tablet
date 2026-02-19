from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget,
                             QVBoxLayout,
                             QFormLayout,
                             QLabel,
                             QGroupBox,
                             QSizePolicy,
                             QPushButton,
                             QLayout)

from data import Card, KanaCard, KanjiCard, PhraseCard
from .drawing_display import DrawingDisplay



def _make_label(value: object) -> QLabel:
    lbl = QLabel(str(value) if value is not None else "")
    lbl.setWordWrap(True)
    lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return lbl



class CardInfoView(QWidget):
    def __init__(self, parent=None,
                       drawing_width: int = 100,
                       drawing_height: int = 100):
        super().__init__(parent)
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._drawing_width = drawing_width
        self._drawing_height = drawing_height

    def _make_card_box(self, c: Card) -> QGroupBox:
        card_box = QGroupBox('General Information')
        form = QFormLayout(card_box)
        form.addRow('ID: ', _make_label(c.id))
        form.addRow('Study ID: ', _make_label(c.study_id))
        form.addRow('Due Date: ', _make_label(c.due_date))
        form.addRow('Due Date Increment: ', _make_label(c.due_date_increment))
        if c.tags == '' or c.tags == None:
            form.addRow('Tags: ', _make_label(c.tags))
        return card_box



    def _make_drawing_section(self) -> tuple[QGroupBox, DrawingDisplay]:
        box = QGroupBox("Drawing")
        v = QVBoxLayout(box)

        # --- top bar ---
        restart_btn = QPushButton("Redraw")
        restart_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        v.addWidget(restart_btn)

        # --- drawing widget ---
        disp = DrawingDisplay(milisec_per_point=10,
                              width=self._drawing_width,
                              height=self._drawing_height)
        disp.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        v.addWidget(disp, 1)  # stretch=1 so it fills remaining space

        # wire button to the display instance
        restart_btn.clicked.connect(disp.restart)

        return box, disp



    def _make_kana_box(self, kc: KanaCard) -> QGroupBox:
        box = QGroupBox("Kana Card Information")
        form = QFormLayout(box)

        form.addRow("Kana: ", _make_label(kc.kana))
        form.addRow("Romaji: ", _make_label(kc.romaji))

        if kc.drawing:
            d_box, d_display = self._make_drawing_section()
            d_display.set_strokes(kc.drawing.strokes)
            d_display.restart()
            form.addRow(d_box)
        else:
            form.addRow('Drawing: ', _make_label('None'))

        return box



    def _make_kanji_box(self, kc: KanjiCard) -> QGroupBox:
        box = QGroupBox("Kanji Card Information")
        form = QFormLayout(box)

        form.addRow("Kanji: ", _make_label(kc.kanji))
        if kc.on_yomi:
            form.addRow("On-yomi: ", _make_label(kc.on_yomi))
        if kc.kun_yomi:
            form.addRow("Kun-yomi: ", _make_label(kc.kun_yomi))
        form.addRow("Meaning: ", _make_label(kc.meaning))

        if kc.drawing:
            d_box, d_display = self._make_drawing_section()
            d_display.set_strokes(kc.drawing.strokes)
            d_display.restart()
            form.addRow(d_box)
        else:
            form.addRow('Drawing: ', _make_label('None'))
        

        return box



    def _make_phrase_box(self, pc: PhraseCard) -> QGroupBox:
        box = QGroupBox("Phrase Information")
        form = QFormLayout(box)

        if pc.kanji_phrase:
            form.addRow("Kanji Phrase: ", _make_label(pc.kanji_phrase))
            
        if pc.kana_phrase:
            form.addRow("Kana Phrase: ", _make_label(pc.kana_phrase))
            
        form.addRow("Meaning: ", _make_label(pc.meaning))
        form.addRow("Grammar: ", _make_label(pc.grammar))

        return box



    def _clear_layout(self, layout: QLayout) -> None:
        """
        Remove and delete all widgets and sub-layouts from the given layout.
        """
        while layout.count():
            item = layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout is not None:
                    self._clear_layout(sub_layout)


    
    def set_card(self, obj: KanaCard | KanjiCard | PhraseCard) -> None:
        # 1) Clear existing UI
        self._clear_layout(self._root_layout)

        # 2) Create a container widget for this card
        container = QWidget(self)
        v = QVBoxLayout(container)
        v.setContentsMargins(0, 0, 0, 0)

        # 3) General card box (always shown)
        base_box = self._make_card_box(obj.card)
        v.addWidget(base_box)

        # 4) Specific card box
        if isinstance(obj, KanaCard):
            specific_box = self._make_kana_box(obj)
        elif isinstance(obj, KanjiCard):
            specific_box = self._make_kanji_box(obj)
        else:
            specific_box = self._make_phrase_box(obj)

        v.addWidget(specific_box, 1)

        # 6) Add to root layout
        self._root_layout.addWidget(container)
