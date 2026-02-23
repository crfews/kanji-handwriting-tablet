# Thoughts: drawing widget, romaji, submit function, clear function? 
# answer widget
#stacked widget
# when submit -> change current widget. 
# 
#
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QStackedWidget, QWidget
from typing import Iterator, Optional
from data import KanaCard, query_reviewable_kana_card
from gui.widgets.writing_widgets import CharacterDrawing
from gui.widgets.drawing_display import DrawingDisplay
from logic.drawing_utils import bin_drawing_respose



class ReviewKanaPage(QtWidgets.QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)

        self.stack = QStackedWidget()

        self.kana_question_widget = KanaQuestionWidget(self.stack)
        self.kana_answer_widget = KanaAnswerWidget(self.stack)
        self._nothingHere = QLabel('Nothing To Study')

        self.stack.addWidget(self._nothingHere)
        self.stack.addWidget(self.kana_question_widget)
        self.stack.addWidget(self.kana_answer_widget)
        
        layout.addWidget(self.stack)
        self.kana_question_widget.submitted.connect(self.show_answer)
        self.kana_answer_widget.next_signal.connect(self.next_kana)

        # Feth all of the kana we want to review
        self._cards = list(query_reviewable_kana_card())
        self._current_card_index = 0
        if len(self._cards) > 0:
            self.kana_question_widget.set_kana(self._cards[self._current_card_index])
            self.kana_answer_widget.set_kana(self._cards[self._current_card_index])
            
            # Setup the graphical display of the page
            self.stack.setCurrentWidget(self.kana_question_widget)
        else:
            self.stack.setCurrentWidget(self._nothingHere)



    def show_answer(self, drawing: list[list[float]]):
        assert drawing is not None

        correct_strokes = self._cards[self._current_card_index].drawing
        assert correct_strokes
        correct_strokes = correct_strokes.strokes

        print(bin_drawing_respose(drawing, correct_strokes))

        self.kana_answer_widget.answer_provided(drawing)
        
        self.stack.setCurrentWidget(self.kana_answer_widget)
    #   controller
    # I can have a static function that is called by the callback function "onsubmit" in KanaWuestionWidget

    
    def next_kana(self):
        self._current_card_index += 1
        if self._current_card_index < len(self._cards):
            self.kana_question_widget.set_kana(self._cards[self._current_card_index])
            self.kana_answer_widget.set_kana(self._cards[self._current_card_index])
            
            self.stack.setCurrentWidget(self.kana_question_widget)
        else:
            self.stack.setCurrentWidget(self._nothingHere)
    



class KanaQuestionWidget(QtWidgets.QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(12)

        self._it: Optional[Iterator[list[KanaCard]]] = None
        self._current: Optional[KanaCard] = None
        self._submitted_for_current = False
        
        #romaji label
        self.romaji_label = QtWidgets.QLabel("'A'", self)
        self.romaji_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        f = self.romaji_label.font()
        f.setPointSize(64)
        f.setBold(True)
        self.romaji_label.setFont(f)
        root.addWidget(self.romaji_label)

        self.drawing = CharacterDrawing(parent=self, on_submitted=self._on_submitted, on_cleared=self._on_cleared)
        root.addWidget(self.drawing)

    submitted = QtCore.pyqtSignal(list)

    def set_kana(self, c: KanaCard) -> None:
        self.romaji_label.setText(c.romaji)
    
    # _on_submitted here - calls
    def _on_submitted(self, drawing: list[list[float]]) -> None:
        self.submitted.emit(drawing)
        self.drawing.force_clear()


    def _on_cleared(self) -> None:
        return



        



class KanaAnswerWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(12)

        # Correct/Not Correct label shown on answer widget
        self.correct_label = QtWidgets.QLabel('Correct/Not Correct', self)
        self.correct_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        f = self.correct_label.font()
        f.setPointSize(32)
        f.setBold(True)
        self.correct_label.setFont(f)
        root.addWidget(self.correct_label)

        # Add the side by side of the user's drawing and the DB's drawing
        self._user_drawing = DrawingDisplay(self)
        self._db_drawing = DrawingDisplay(self)
        self._side_by_side = QWidget(self)
        side_by_side_root = QHBoxLayout(self._side_by_side)
        side_by_side_root.addWidget(self._db_drawing)
        side_by_side_root.addWidget(self._user_drawing)
        root.addWidget(self._side_by_side)
        
        # Next button 
        self.next_button = QtWidgets.QPushButton('Next', self)
        self.next_button.clicked.connect(self.next_clicked)
        root.addWidget(self.next_button)

        

    next_signal = QtCore.pyqtSignal()

    def answer_provided(self, s: list[list[float]]) -> None:
        self._user_drawing.set_strokes(s)
        self._user_drawing.restart()
        self._db_drawing.restart()
        
    def set_kana(self, c: KanaCard) -> None:
        s = c.drawing
        assert s
        s = s.strokes
        self._db_drawing.set_strokes(s)
        self.correct_label.setText(c.kana)
        pass
    
    def next_clicked(self) -> None:
        self.next_signal.emit()

        
        







