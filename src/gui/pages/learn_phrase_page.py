from __future__ import annotations

from typing import Iterator, Optional

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColorConstants, QPalette

from data import PhraseCard
from data.database import maybe_connection
from data.queries import query_learnable_phrase_cards

from logic.grade_handwriting import grade_strokes

# Import your new widgets (adjust import paths to match your project)
# - GenkouyoushiWidgets: user input grid (captures strokes per character)
# - GenkouyoushiDrawingDisplay: canonical animated display for a string
from gui.widgets.writing_widgets import GenkouyoushiWidgets  # :contentReference[oaicite:2]{index=2}
from gui.widgets.genkouyoushi_drawing_display import GenkouyoushiDrawingDisplay  # built from DrawingDisplay :contentReference[oaicite:3]{index=3}


def _pick_target_string(card: PhraseCard) -> str:
    """
    Prefer kanji_phrase when available, otherwise kana_phrase.
    Empty string means "nothing to practice" (we'll treat as done/skip).
    """
    kp = (card.kanji_phrase or "").strip()
    if kp:
        return kp
    return (card.kana_phrase or "").strip()


class LearnPhrasePage(QtWidgets.QWidget):
    """
    Learn session (Phrases):
      - iterates query_learnable_phrase_cards()
      - shows fields: kanji phrase, kana phrase, grammar, meaning
      - shows canonical GenkouyoushiDrawingDisplay for the target string
      - user writes into GenkouyoushiWidgets (same genkou layout)
      - user cannot proceed until EVERY character grades 0 vs target char
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
        # Main learn page
        # -----------------------
        self.q_page = QtWidgets.QWidget(self.stack)
        q_root = QtWidgets.QVBoxLayout(self.q_page)
        q_root.setSpacing(10)

        # Header: phrase (kanji/kana)
        self.kanji_phrase_label = QtWidgets.QLabel("", self.q_page)
        self.kanji_phrase_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        f = self.kanji_phrase_label.font()
        f.setPointSize(28)
        f.setBold(True)
        self.kanji_phrase_label.setFont(f)
        self.kanji_phrase_label.setWordWrap(True)

        self.kana_phrase_label = QtWidgets.QLabel("", self.q_page)
        self.kana_phrase_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.kana_phrase_label.setWordWrap(True)

        self.grammar_label = QtWidgets.QLabel("", self.q_page)
        self.grammar_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.grammar_label.setWordWrap(True)

        self.meaning_label = QtWidgets.QLabel("", self.q_page)
        self.meaning_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.meaning_label.setWordWrap(True)

        self.q_status = QtWidgets.QLabel("Press Start to begin.", self.q_page)
        self.q_status.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.q_status.setWordWrap(True)

        q_root.addWidget(self.kanji_phrase_label)
        q_root.addWidget(self.kana_phrase_label)
        q_root.addWidget(self.grammar_label)
        q_root.addWidget(self.meaning_label)
        q_root.addWidget(self.q_status)

        # Panels: canonical (left) + user drawing (right)
        panels = QtWidgets.QHBoxLayout()
        panels.setSpacing(12)

        left_box = QtWidgets.QGroupBox("Correct writing", self.q_page)
        left_layout = QtWidgets.QVBoxLayout(left_box)
        left_layout.setSpacing(8)

        # Canonical display (string)
        # row_cap is configurable; keep it consistent with the input grid.
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
        self.done_page = QtWidgets.QLabel("Nothing to learn.", self.stack)
        self.done_page.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.stack.addWidget(self.done_page)
        self.stack.addWidget(self.q_page)
        self.stack.setCurrentWidget(self.done_page)

        # Defaults for status label reset
        self._q_status_default_font = self.q_status.font()
        self._q_status_default_palette = self.q_status.palette()

    # -----------------------
    # Session control
    # -----------------------

    def _reset_status_style(self) -> None:
        self.q_status.setFont(self._q_status_default_font)
        self.q_status.setPalette(self._q_status_default_palette)

    def showEvent(self, a0):
        super().showEvent(a0)
        if self._cards is None:  # lazy load once when shown
            self.start()

    @QtCore.pyqtSlot()
    def start(self) -> None:
        if self._cards is None:
            self._cards = query_learnable_phrase_cards()

        self.next_card()

    @QtCore.pyqtSlot()
    def restart(self) -> None:
        self._cards = None
        self._current = None
        self._target = ""

        self.drawing.force_clear()
        self.canonical.set_text("")

        self.kanji_phrase_label.setText("")
        self.kana_phrase_label.setText("")
        self.grammar_label.setText("")
        self.meaning_label.setText("")
        self._reset_status_style()
        self.q_status.setText("Press Start to begin.")
        self.stack.setCurrentWidget(self.done_page)

    @QtCore.pyqtSlot()
    def next_card(self) -> None:
        self._reset_status_style()

        if self._cards is None:
            self.done_page.setText("✓ No more learnable phrase cards.")
            self.stack.setCurrentWidget(self.done_page)
            return

        try:
            self._current = next(self._cards)
        except StopIteration:
            self._current = None
            self._cards = None
            self.done_page.setText("✓ No more learnable phrase cards.")
            self.stack.setCurrentWidget(self.done_page)
            return

        # Populate info fields
        kp = (self._current.kanji_phrase or "").strip()
        ka = (self._current.kana_phrase or "").strip()
        gr = (self._current.grammar or "").strip()
        mn = (self._current.meaning or "").strip()

        self.kanji_phrase_label.setText(kp if kp else "—")
        self.kana_phrase_label.setText(ka if ka else "")
        self.grammar_label.setText(gr if gr else "")
        self.meaning_label.setText(mn if mn else "")

        # Target string decides what they must write
        self._target = _pick_target_string(self._current)

        if not self._target:
            # Nothing to practice: mark learned and continue
            self._current.card.study_id = 1
            self._current.sync()
            self.next_card()
            return

        # Configure canonical + input grids to match target length
        self.canonical.set_row_cap(self._row_cap)
        self.canonical.set_text(self._target)

        self.drawing.set_row_cap(self._row_cap)
        self.drawing.set_count(len(self._target))
        self.drawing.force_clear()

        self.q_status.setText("Copy the phrase exactly. You must get every character correct (grade 0) to proceed.")
        self.stack.setCurrentWidget(self.q_page)

    # -----------------------
    # Drawing callbacks
    # -----------------------

    def _on_cleared(self) -> None:
        if self._current is None or not self._target:
            return
        self._reset_status_style()
        self.q_status.setText("Cleared. Try again, then Submit.")

    def _on_submitted(self, seq: list[list[list[float]]]) -> None:
        """
        seq[i] is the strokes for character i in the target string.
        Enforce: all characters must grade 0.
        """
        if self._current is None or not self._target:
            return

        if len(seq) != len(self._target):
            # Should not happen if set_count() tracks target length, but guard anyway.
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

        # Must be perfect: all 0
        if all(g == 0 for g in grades):
            pal.setColor(QPalette.ColorRole.WindowText, QColorConstants.Green)
            self.q_status.setPalette(pal)
            self.q_status.setText("Correct — moving on!")

            # Mark learned
            self._current.card.study_id = 1
            self._current.sync()

            self.next_card()
            return

        # Not all correct -> block progress
        first_bad = next(i for i, g in enumerate(grades) if g != 0)
        gb = grades[first_bad]

        if gb == 1:
            pal.setColor(QPalette.ColorRole.WindowText, QColorConstants.Yellow)
            msg = f"Close on character {first_bad + 1}/{len(grades)} (‘{self._target[first_bad]}’) — try again."
        else:
            pal.setColor(QPalette.ColorRole.WindowText, QColorConstants.Red)
            msg = f"Incorrect on character {first_bad + 1}/{len(grades)} (‘{self._target[first_bad]}’) — try again."

        self.q_status.setPalette(pal)
        self.q_status.setText(msg)

        # Force retry: clear all (simple + consistent with your kanji flow)
        self.drawing.force_clear()


