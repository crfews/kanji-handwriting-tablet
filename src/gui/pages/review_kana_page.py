# Thoughts: drawing widget, romaji, submit function, clear function? 
# answer widget
#stacked widget
# when submit -> change current widget. 
# 
#
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QStackedWidget
from typing import Iterator, Optional
from data import KanaCard, Drawing
from gui.widgets.writing_widgets import CharacterDrawing




class ReviewKanaPage(QtWidgets.QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)

        self.stack = QStackedWidget()

        self.kana_question_widget = KanaQuestionWidget(self.stack)
        self.kana_answer_widget = KanaAnswerWidget(self.stack)

        self.stack.addWidget(self.kana_question_widget)
        self.stack.addWidget(self.kana_answer_widget)
        

        layout.addWidget(self.stack)

        self.stack.setCurrentWidget(self.kana_question_widget)

        self.kana_question_widget.submitted.connect(self.flip_to_answer)
        self.kana_answer_widget.next_signal.connect(self.flip_to_question)

    def flip_to_answer(self):
        print('flipped to answer')
        self.stack.setCurrentWidget(self.kana_answer_widget)
    #   controller
    # I can have a static function that is called by the callback function "onsubmit" in KanaWuestionWidget

    def flip_to_question(self):
        print('flip to question')
        self.stack.setCurrentWidget(self.kana_question_widget)
    

##new controller class? with static method flip
#class Controller():
#    def __init__(self):
#        return
#    
#    @staticmethod
#    def flip(stack):
        
    





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

    submitted = QtCore.pyqtSignal()

    # _on_submitted here - calls
    def _on_submitted(self) -> None:
        self.submitted.emit()
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

        # Next button 
        self.next_button = QtWidgets.QPushButton('Next', self)
        self.next_button.clicked.connect(self.next_clicked)
        root.addWidget(self.next_button)

    next_signal = QtCore.pyqtSignal()

    def next_clicked(self) -> None:
        self.next_signal.emit()

        
        







