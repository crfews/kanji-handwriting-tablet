from __future__ import annotations

from typing import Optional

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColorConstants, QPalette
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QStackedWidget, QWidget

from data import KanaCard
from data.queries import query_reviewable_kana_card

from gui.widgets.writing_widgets import CharacterDrawing
from gui.widgets.drawing_display import DrawingDisplay

from logic.grade_handwriting import grade_strokes
from logic.review_card import review_card_bin

def _set_grade_badge(lbl: QtWidgets.QLabel, grade: int) -> None:
    # If emoji rendering is flaky on your system, swap these to: "✔", "●", "✖"
    if grade == 0:
        lbl.setText("✅")
        lbl.setStyleSheet("font-size: 64px; color: #2e7d32;")
    elif grade == 1:
        lbl.setText("🟡")
        lbl.setStyleSheet("font-size: 64px; color: #f9a825;")
    else:
        lbl.setText("❌")
        lbl.setStyleSheet("font-size: 64px; color: #c62828;")


class ReviewKanaPage(QtWidgets.QWidget):
    """
    Review session (Kana):
      - lazy loads cards on first showEvent
      - does NOT create drawing widgets unless there is at least one reviewable card
      - user must score grade==0 to proceed to next card
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        self.stack = QStackedWidget(self)
        layout.addWidget(self.stack)

        self._nothing_here = QLabel("Nothing To Study", self.stack)
        self._nothing_here.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.stack.addWidget(self._nothing_here)
        self.stack.setCurrentWidget(self._nothing_here)

        self._loaded_once = False
        self._cards: list[KanaCard] = []
        self._current_card_index = 0

        # These are created lazily ONLY when we have cards
        self.kana_question_widget: Optional[KanaQuestionWidget] = None
        self.kana_answer_widget: Optional[KanaAnswerWidget] = None

        # Attempt state
        self._attempts_on_current = 0
        self._first_success_try: Optional[int] = None
        
    def showEvent(self, a0) -> None:
        super().showEvent(a0)

        # Only load once on first visibility
        if not self._loaded_once:
            self._loaded_once = True
            self._load_if_needed()

    def _load_if_needed(self) -> None:
        self._cards = list(query_reviewable_kana_card())
        self._current_card_index = 0

        self._attempts_on_current = 0
        self._first_success_try = None
        
        if not self._cards:
            self.stack.setCurrentWidget(self._nothing_here)
            return

        # Create widgets ONLY now (since we know something exists)
        self.kana_question_widget = KanaQuestionWidget(self.stack)
        self.kana_answer_widget = KanaAnswerWidget(self.stack)

        self.stack.addWidget(self.kana_question_widget)
        self.stack.addWidget(self.kana_answer_widget)

        self.kana_question_widget.submitted.connect(self.show_answer)
        self.kana_answer_widget.next_signal.connect(self.next_kana)
        self.kana_answer_widget.try_again_signal.connect(self.try_again)

        c = self._cards[self._current_card_index]
        self.kana_question_widget.set_kana(c)
        self.kana_answer_widget.set_kana(c)
        self.stack.setCurrentWidget(self.kana_question_widget)

    def show_answer(self, drawing: list[list[float]]) -> None:
        # Ignore empty submits
        if not drawing:
            return
        if not self._cards:
            return
        assert self.kana_answer_widget is not None


        self._attempts_on_current += 1


        c = self._cards[self._current_card_index]
        g = grade_strokes(drawing, c.kana)


        if g == 0 and self._first_success_try is None:
            self._first_success_try = self._attempts_on_current

        if self._first_success_try == 1:
            review_card_bin(c.card, 0)
        elif self._first_success_try == 2:
            review_card_bin(c.card,1)
        elif self._first_success_try is not None and self._first_success_try >= 3:
            review_card_bin(c.card,2)
        
        self.kana_answer_widget.answer_provided(drawing, g)
        self.stack.setCurrentWidget(self.kana_answer_widget)



    def try_again(self) -> None:
        # Go back to the question widget for the same card
        if not self._cards:
            self.stack.setCurrentWidget(self._nothing_here)
            return
        assert self.kana_question_widget is not None
        assert self.kana_answer_widget is not None

        c = self._cards[self._current_card_index]
        self.kana_question_widget.set_kana(c)
        self.stack.setCurrentWidget(self.kana_question_widget)



    def next_kana(self) -> None:
        if not self._cards:
            self.stack.setCurrentWidget(self._nothing_here)
            return
        assert self.kana_question_widget is not None
        assert self.kana_answer_widget is not None

        self._current_card_index += 1
        if self._current_card_index < len(self._cards):
            c = self._cards[self._current_card_index]
            self._attempts_on_current = 0
            self._first_success_try = None
            
            self.kana_question_widget.set_kana(c)
            self.kana_answer_widget.set_kana(c)
            self.stack.setCurrentWidget(self.kana_question_widget)
        else:
            self.stack.setCurrentWidget(self._nothing_here)


class KanaQuestionWidget(QtWidgets.QWidget):
    submitted = QtCore.pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(12)

        self.romaji_label = QtWidgets.QLabel("", self)
        self.romaji_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        f = self.romaji_label.font()
        f.setPointSize(64)
        f.setBold(True)
        self.romaji_label.setFont(f)
        root.addWidget(self.romaji_label)

        self.drawing = CharacterDrawing(
            parent=self,
            on_submitted=self._on_submitted,
            on_cleared=self._on_cleared,
        )
        root.addWidget(self.drawing)

    def set_kana(self, c: KanaCard) -> None:
        self.romaji_label.setText(c.romaji or "")
        self.drawing.force_clear()

    def _on_submitted(self, drawing: list[list[float]]) -> None:
        self.submitted.emit(drawing)
        self.drawing.force_clear()

    def _on_cleared(self) -> None:
        return


class KanaAnswerWidget(QtWidgets.QWidget):
    next_signal = QtCore.pyqtSignal()
    try_again_signal = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._has_db_strokes = False
        self._last_grade: Optional[int] = None

        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(12)

        self.badge = QtWidgets.QLabel("", self)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        root.addWidget(self.badge)

        self.feedback_label = QtWidgets.QLabel("", self)
        self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        fb = self.feedback_label.font()
        fb.setPointSize(24)
        fb.setBold(True)
        self.feedback_label.setFont(fb)
        root.addWidget(self.feedback_label)

        self.correct_label = QtWidgets.QLabel("", self)
        self.correct_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        f = self.correct_label.font()
        f.setPointSize(32)
        f.setBold(True)
        self.correct_label.setFont(f)
        root.addWidget(self.correct_label)

        # Side-by-side: canonical (DB) vs user
        self._db_drawing = DrawingDisplay(self)
        self._user_drawing = DrawingDisplay(self)

        side = QWidget(self)
        side_root = QHBoxLayout(side)
        side_root.addWidget(self._db_drawing)
        side_root.addWidget(self._user_drawing)
        root.addWidget(side)

        # Buttons row
        btn_row = QtWidgets.QHBoxLayout()

        self.replay_btn = QtWidgets.QPushButton("Replay correct drawing", self)
        self.replay_btn.clicked.connect(self._replay_db)

        self.try_again_btn = QtWidgets.QPushButton("Try again", self)
        self.try_again_btn.clicked.connect(self._try_again_clicked)

        self.next_button = QtWidgets.QPushButton("Next", self)
        self.next_button.clicked.connect(self.next_clicked)

        btn_row.addWidget(self.replay_btn)
        btn_row.addWidget(self.try_again_btn)
        btn_row.addWidget(self.next_button)
        root.addLayout(btn_row)

        self.replay_btn.setEnabled(False)
        self.next_button.setEnabled(False)  # must earn it

    def set_kana(self, c: KanaCard) -> None:
        self.correct_label.setText(c.kana)

        # Reset feedback
        self._last_grade = None
        self.badge.setText("")
        self.badge.setStyleSheet("")
        self.feedback_label.setText("")
        # reset palette (in case it was colored)
        self.feedback_label.setPalette(self.style().standardPalette())

        # Load canonical drawing ONLY if present; NEVER call set_strokes([])
        self._has_db_strokes = False
        d = c.drawing
        if d is not None and getattr(d, "strokes", None):
            self._db_drawing.set_strokes(d.strokes)
            self._db_drawing.restart()
            self._has_db_strokes = True
        else:
            self._db_drawing.stop()

        # User drawing: leave blank; do NOT call set_strokes([]) (would crash)
        self._user_drawing.stop()

        self.replay_btn.setEnabled(self._has_db_strokes)
        self.next_button.setEnabled(False)

    def answer_provided(self, s: list[list[float]], grade: int) -> None:
        self._last_grade = grade
        _set_grade_badge(self.badge, grade)

        # Feedback text + color (matches learning page semantics)
        pal = self.feedback_label.palette()
        if grade == 0:
            pal.setColor(QPalette.ColorRole.WindowText, QColorConstants.Green)
            self.feedback_label.setText("Correct")
        elif grade == 1:
            pal.setColor(QPalette.ColorRole.WindowText, QColorConstants.Yellow)
            self.feedback_label.setText("Close")
        else:
            pal.setColor(QPalette.ColorRole.WindowText, QColorConstants.Red)
            self.feedback_label.setText("Incorrect")
        self.feedback_label.setPalette(pal)

        # User drawing is real strokes here; safe to set
        if s:
            self._user_drawing.set_strokes(s)
            self._user_drawing.restart()
        else:
            self._user_drawing.stop()

        if self._has_db_strokes:
            self._db_drawing.restart()

        # ENFORCE mastery: cannot proceed unless grade==0
        self.next_button.setEnabled(grade == 0)

    def _replay_db(self) -> None:
        if self._has_db_strokes:
            self._db_drawing.restart()

    def _try_again_clicked(self) -> None:
        self.try_again_signal.emit()

    def next_clicked(self) -> None:
        # extra guard (in case someone triggers programmatically)
        if self._last_grade != 0:
            return
        self.next_signal.emit()

















































# from __future__ import annotations

# from typing import Optional

# from PyQt6 import QtCore, QtWidgets
# from PyQt6.QtCore import Qt
# from PyQt6.QtWidgets import QHBoxLayout, QLabel, QStackedWidget, QWidget

# from data import KanaCard
# from data.queries import query_reviewable_kana_card

# from gui.widgets.writing_widgets import CharacterDrawing
# from gui.widgets.drawing_display import DrawingDisplay

# from logic.grade_handwriting import grade_strokes


# def _set_grade_badge(lbl: QtWidgets.QLabel, grade: int) -> None:
#     # Keep as text; if emoji fonts are flaky, swap these for "✔", "●", "✖"
#     if grade == 0:
#         lbl.setText("✅")
#         lbl.setStyleSheet("font-size: 64px; color: #2e7d32;")
#     elif grade == 1:
#         lbl.setText("🟡")
#         lbl.setStyleSheet("font-size: 64px; color: #f9a825;")
#     else:
#         lbl.setText("❌")
#         lbl.setStyleSheet("font-size: 64px; color: #c62828;")


# class ReviewKanaPage(QtWidgets.QWidget):
#     """
#     Review session (Kana):
#       - lazy loads cards on first showEvent
#       - does NOT create drawing widgets unless there is at least one reviewable card
#     """

#     def __init__(self, parent=None):
#         super().__init__(parent)

#         layout = QtWidgets.QVBoxLayout(self)
#         self.stack = QStackedWidget(self)
#         layout.addWidget(self.stack)

#         self._nothing_here = QLabel("Nothing To Study", self.stack)
#         self._nothing_here.setAlignment(Qt.AlignmentFlag.AlignHCenter)
#         self.stack.addWidget(self._nothing_here)
#         self.stack.setCurrentWidget(self._nothing_here)

#         self._loaded_once = False
#         self._cards: list[KanaCard] = []
#         self._current_card_index = 0

#         # These are created lazily ONLY when we have cards
#         self.kana_question_widget: Optional[KanaQuestionWidget] = None
#         self.kana_answer_widget: Optional[KanaAnswerWidget] = None

#     def showEvent(self, a0) -> None:
#         super().showEvent(a0)

#         # Only load once on first visibility
#         if not self._loaded_once:
#             self._loaded_once = True
#             self._load_if_needed()

#     def _load_if_needed(self) -> None:
#         self._cards = list(query_reviewable_kana_card())
#         self._current_card_index = 0

#         if not self._cards:
#             self.stack.setCurrentWidget(self._nothing_here)
#             return

#         # Create widgets ONLY now (since we know something exists)
#         self.kana_question_widget = KanaQuestionWidget(self.stack)
#         self.kana_answer_widget = KanaAnswerWidget(self.stack)

#         self.stack.addWidget(self.kana_question_widget)
#         self.stack.addWidget(self.kana_answer_widget)

#         self.kana_question_widget.submitted.connect(self.show_answer)
#         self.kana_answer_widget.next_signal.connect(self.next_kana)

#         c = self._cards[self._current_card_index]
#         self.kana_question_widget.set_kana(c)
#         self.kana_answer_widget.set_kana(c)
#         self.stack.setCurrentWidget(self.kana_question_widget)

#     def show_answer(self, drawing: list[list[float]]) -> None:
#         # Ignore empty submits
#         if not drawing:
#             return
#         if not self._cards:
#             return
#         assert self.kana_answer_widget is not None

#         c = self._cards[self._current_card_index]
#         g = grade_strokes(drawing, c.kana)

#         self.kana_answer_widget.answer_provided(drawing, g)
#         self.stack.setCurrentWidget(self.kana_answer_widget)

#     def next_kana(self) -> None:
#         if not self._cards:
#             self.stack.setCurrentWidget(self._nothing_here)
#             return
#         assert self.kana_question_widget is not None
#         assert self.kana_answer_widget is not None

#         self._current_card_index += 1
#         if self._current_card_index < len(self._cards):
#             c = self._cards[self._current_card_index]
#             self.kana_question_widget.set_kana(c)
#             self.kana_answer_widget.set_kana(c)
#             self.stack.setCurrentWidget(self.kana_question_widget)
#         else:
#             self.stack.setCurrentWidget(self._nothing_here)


# class KanaQuestionWidget(QtWidgets.QWidget):
#     submitted = QtCore.pyqtSignal(list)

#     def __init__(self, parent=None):
#         super().__init__(parent)

#         root = QtWidgets.QVBoxLayout(self)
#         root.setSpacing(12)

#         self.romaji_label = QtWidgets.QLabel("", self)
#         self.romaji_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
#         f = self.romaji_label.font()
#         f.setPointSize(64)
#         f.setBold(True)
#         self.romaji_label.setFont(f)
#         root.addWidget(self.romaji_label)

#         self.drawing = CharacterDrawing(
#             parent=self,
#             on_submitted=self._on_submitted,
#             on_cleared=self._on_cleared,
#         )
#         root.addWidget(self.drawing)

#     def set_kana(self, c: KanaCard) -> None:
#         self.romaji_label.setText(c.romaji or "")
#         self.drawing.force_clear()

#     def _on_submitted(self, drawing: list[list[float]]) -> None:
#         self.submitted.emit(drawing)
#         self.drawing.force_clear()

#     def _on_cleared(self) -> None:
#         return


# class KanaAnswerWidget(QtWidgets.QWidget):
#     next_signal = QtCore.pyqtSignal()

#     def __init__(self, parent=None):
#         super().__init__(parent)

#         self._has_db_strokes = False

#         root = QtWidgets.QVBoxLayout(self)
#         root.setSpacing(12)

#         self.badge = QtWidgets.QLabel("", self)
#         self.badge.setAlignment(Qt.AlignmentFlag.AlignHCenter)
#         root.addWidget(self.badge)

#         self.correct_label = QtWidgets.QLabel("", self)
#         self.correct_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
#         f = self.correct_label.font()
#         f.setPointSize(32)
#         f.setBold(True)
#         self.correct_label.setFont(f)
#         root.addWidget(self.correct_label)

#         # Side-by-side: canonical (DB) vs user
#         self._db_drawing = DrawingDisplay(self)
#         self._user_drawing = DrawingDisplay(self)

#         side = QWidget(self)
#         side_root = QHBoxLayout(side)
#         side_root.addWidget(self._db_drawing)
#         side_root.addWidget(self._user_drawing)
#         root.addWidget(side)

#         # Replay canonical animation (only meaningful if DB strokes exist)
#         self.replay_btn = QtWidgets.QPushButton("Replay correct drawing", self)
#         self.replay_btn.clicked.connect(self._replay_db)
#         root.addWidget(self.replay_btn)

#         self.next_button = QtWidgets.QPushButton("Next", self)
#         self.next_button.clicked.connect(self.next_clicked)
#         root.addWidget(self.next_button)

#         # Start disabled until a card is set
#         self.replay_btn.setEnabled(False)

#     def set_kana(self, c: KanaCard) -> None:
#         self.correct_label.setText(c.kana)

#         # Reset badge
#         self.badge.setText("")
#         self.badge.setStyleSheet("")

#         # Load canonical drawing ONLY if present; NEVER call set_strokes([])
#         self._has_db_strokes = False
#         d = c.drawing
#         if d is not None and getattr(d, "strokes", None):
#             self._db_drawing.set_strokes(d.strokes)
#             self._db_drawing.restart()
#             self._has_db_strokes = True
#         else:
#             # leave blank, stop animation if any
#             self._db_drawing.stop()

#         # User drawing: leave blank; do NOT call set_strokes([]) (would crash)
#         self._user_drawing.stop()

#         self.replay_btn.setEnabled(self._has_db_strokes)

#     def answer_provided(self, s: list[list[float]], grade: int) -> None:
#         _set_grade_badge(self.badge, grade)

#         # User drawing is real strokes here; safe to set
#         if s:
#             self._user_drawing.set_strokes(s)
#             self._user_drawing.restart()
#         else:
#             self._user_drawing.stop()

#         # Optionally replay canonical when showing answer
#         if self._has_db_strokes:
#             self._db_drawing.restart()

#     def _replay_db(self) -> None:
#         if self._has_db_strokes:
#             self._db_drawing.restart()

#     def next_clicked(self) -> None:
#         self.next_signal.emit()

