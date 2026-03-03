# review_phrase_page.py
from __future__ import annotations

from typing import Iterator, Optional

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColorConstants, QPalette

from data import PhraseCard
from data.queries import query_reviewable_phrase_cards  # <-- adjust name if different
from logic.grade_handwriting import grade_strokes

from gui.widgets.writing_widgets import GenkouyoushiWidgets
from gui.widgets.genkouyoushi_drawing_display import GenkouyoushiDrawingDisplay

from logic.review_card import review_card_bin

def _pick_target_string(card: PhraseCard) -> str:
    """Prefer kanji_phrase when available; else kana_phrase; else empty."""
    kp = (card.kanji_phrase or "").strip()
    if kp:
        return kp
    return (card.kana_phrase or "").strip()


class ReviewPhrasePage(QtWidgets.QWidget):
    """
    Review session (Phrases):
      - iterates query_reviewable_phrase_cards()
      - shows meaning + grammar (no phrase shown)
      - shows canonical GenkouyoushiDrawingDisplay for target string (left)
      - user writes into GenkouyoushiWidgets (right)
      - user cannot proceed until EVERY character grades 0 vs target char
      - if incorrect/close -> forced rewrite (same card)
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._cards: Optional[Iterator[PhraseCard]] = None
        self._current: Optional[PhraseCard] = None
        self._target: str = ""

        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(12)

        self.stack = QtWidgets.QStackedWidget(self)
        root.addWidget(self.stack, 1)

        # -----------------------
        # Main review page
        # -----------------------
        self.q_page = QtWidgets.QWidget(self.stack)
        q_root = QtWidgets.QVBoxLayout(self.q_page)
        q_root.setSpacing(10)

        # Big “prompt” marker (no phrase shown)
        self.prompt_label = QtWidgets.QLabel("—", self.q_page)
        self.prompt_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        f = self.prompt_label.font()
        f.setPointSize(28)
        f.setBold(True)
        self.prompt_label.setFont(f)

        self.grammar_label = QtWidgets.QLabel("", self.q_page)
        self.grammar_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.grammar_label.setWordWrap(True)

        self.meaning_label = QtWidgets.QLabel("", self.q_page)
        self.meaning_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.meaning_label.setWordWrap(True)

        self.q_status = QtWidgets.QLabel("Press Start to begin.", self.q_page)
        self.q_status.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.q_status.setWordWrap(True)

        q_root.addWidget(self.prompt_label)
        q_root.addWidget(self.grammar_label)
        q_root.addWidget(self.meaning_label)
        q_root.addWidget(self.q_status)

        # Panels: canonical (left) + user drawing (right)
        panels = QtWidgets.QHBoxLayout()
        panels.setSpacing(12)

        left_box = QtWidgets.QGroupBox("Correct writing", self.q_page)
        left_layout = QtWidgets.QVBoxLayout(left_box)
        left_layout.setSpacing(8)

        self._row_cap = 10
        self.canonical = GenkouyoushiDrawingDisplay(
            text="",
            row_cap=self._row_cap,
            parent=left_box,
            cell_width=120,
            cell_height=120,
            milisec_per_point=10,
        )
        left_layout.addWidget(self.canonical, 1)

        right_box = QtWidgets.QGroupBox("Your writing", self.q_page)
        right_layout = QtWidgets.QVBoxLayout(right_box)
        right_layout.setSpacing(8)

        self.drawing = GenkouyoushiWidgets(
            count=1,
            row_cap=self._row_cap,
            parent=right_box,
            on_submitted=self._on_submitted,
            on_cleared=self._on_cleared,
        )
        right_layout.addWidget(self.drawing, 1)

        panels.addWidget(left_box, 1)
        panels.addWidget(right_box, 1)
        q_root.addLayout(panels, 1)

        # Start/Restart session row
        q_btns = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("Start", self.q_page)
        self.start_btn.clicked.connect(self.start)

        self.restart_btn = QtWidgets.QPushButton("Restart session", self.q_page)
        self.restart_btn.clicked.connect(self.restart)

        q_btns.addWidget(self.start_btn)
        q_btns.addWidget(self.restart_btn)
        q_root.addLayout(q_btns)

        # -----------------------
        # Done/Empty page
        # -----------------------
        self.done_page = QtWidgets.QLabel("Nothing to review.", self.stack)
        self.done_page.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.stack.addWidget(self.done_page)
        self.stack.addWidget(self.q_page)
        self.stack.setCurrentWidget(self.done_page)

        # Defaults for status label reset
        self._q_status_default_font = self.q_status.font()
        self._q_status_default_palette = self.q_status.palette()

        # Attempt state
        self._attempts_on_current = 0
    # -----------------------
    # Session control
    # -----------------------

    def _reset_status_style(self) -> None:
        self.q_status.setFont(self._q_status_default_font)
        self.q_status.setPalette(self._q_status_default_palette)

    def showEvent(self, a0):
        super().showEvent(a0)
        # lazy load once when shown
        if self._cards is None:
            self.start()

    @QtCore.pyqtSlot()
    def start(self) -> None:
        if self._cards is None:
            self._cards = query_reviewable_phrase_cards()
        self.next_card()

    @QtCore.pyqtSlot()
    def restart(self) -> None:
        self._cards = None
        self._current = None
        self._target = ""

        self.drawing.force_clear()
        self.canonical.set_text("")

        self.prompt_label.setText("—")
        self.grammar_label.setText("")
        self.meaning_label.setText("")
        self._reset_status_style()
        self.q_status.setText("Press Start to begin.")
        self.stack.setCurrentWidget(self.done_page)

    @QtCore.pyqtSlot()
    def next_card(self) -> None:
        self._reset_status_style()

        if self._cards is None:
            self.done_page.setText("✓ No more reviewable phrase cards.")
            self.stack.setCurrentWidget(self.done_page)
            return

        try:
            self._current = next(self._cards)
        except StopIteration:
            self._current = None
            self.done_page.setText("✓ No more reviewable phrase cards.")
            self.stack.setCurrentWidget(self.done_page)
            return

        self._attempts_on_current = 0
        target = _pick_target_string(self._current)
        if not target:
            # nothing to write: just skip
            self.next_card()
            return

        self._target = target

        # Update prompt fields (meaning + grammar only)
        self.prompt_label.setText("—")
        self.meaning_label.setText(self._current.meaning or "")
        self.grammar_label.setText(self._current.grammar or "")

        # Update drawing widgets
        self.drawing.force_clear()
        self.drawing.set_count(len(self._target))

        self.canonical.set_text(self._target)

        self.q_status.setText(
            "Write the phrase from the prompt. You must get every character correct (grade 0) to proceed."
        )

        self.stack.setCurrentWidget(self.q_page)

    # -----------------------
    # Drawing callbacks
    # -----------------------

    def _on_cleared(self) -> None:
        if self._current is None:
            return
        self._reset_status_style()
        self.q_status.setText("Cleared. Try again, then Submit.")

    def _on_submitted(self, seq: list[list[list[float]]]) -> None:
        """
        seq: list of character-strokes (left-to-right reading order of the target string)
        """
        if self._current is None:
            return

        if not self._target:
            self._reset_status_style()
            self.q_status.setText("No target phrase loaded. Restart session.")
            return

        if len(seq) != len(self._target):
            self._reset_status_style()
            self.q_status.setText("Internal mismatch: input length does not match target. Restart session.")
            return

        # Check for empty entries first
        for i, strokes in enumerate(seq):
            if not strokes:
                self._reset_status_style()
                self.q_status.setText(f"Character {i + 1}/{len(seq)} is empty — fill every box before submitting.")
                return

        # Grade each character against the corresponding target glyph
        grades: list[int] = []
        for strokes, glyph in zip(seq, self._target, strict=True):
            grades.append(grade_strokes(strokes, glyph))

        # Styling for feedback
        font = self.q_status.font()
        font.setPointSize(20)
        font.setBold(True)
        self.q_status.setFont(font)

        pal = self.q_status.palette()

        self._attempts_on_current += 1

        
        # Must be perfect: all 0
        if all(g == 0 for g in grades):
            pal.setColor(QPalette.ColorRole.WindowText, QColorConstants.Green)
            self.q_status.setPalette(pal)
            self.q_status.setText("Correct — moving on!")

            if self._attempts_on_current == 1:
                review_card_bin(self._current.card, 0)
            elif self._attempts_on_current == 2:
                review_card_bin(self._current.card, 1)
            else:
                review_card_bin(self._current.card, 2)

            # TODO: scheduling hook (mirror review-kana behavior)
            # self._apply_review_result(self._current, grades)

            self.next_card()
            return

        # Not all correct -> block progress
        first_bad = next(i for i, g in enumerate(grades) if g != 0)
        gb = grades[first_bad]

        if gb == 1:
            pal.setColor(QPalette.ColorRole.WindowText, QColorConstants.Yellow)
            msg = f"Close on character {first_bad + 1}/{len(grades)} (‘{self._target[first_bad]}’) — rewrite the whole phrase."
        else:
            pal.setColor(QPalette.ColorRole.WindowText, QColorConstants.Red)
            msg = f"Incorrect on character {first_bad + 1}/{len(grades)} (‘{self._target[first_bad]}’) — rewrite the whole phrase."

        self.q_status.setPalette(pal)
        self.q_status.setText(msg)

        # Force retry (same card)
        self.drawing.force_clear()


