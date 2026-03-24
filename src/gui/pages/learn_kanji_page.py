from __future__ import annotations

from typing import Optional, Iterator

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColorConstants, QPalette

from data import KanjiCard
from data.database import maybe_connection
from data.queries import query_learnable_kanji_cards

from gui.widgets.writing_widgets import CharacterDrawing
from gui.widgets.drawing_display import DrawingDisplay
from logic.grade_handwriting import grade_strokes


class LearnKanjiPage(QtWidgets.QWidget):
    """
    Learn session (Kanji):
      - iterates query_learnable_kanji_cards()
      - shows canonical drawing (left) + user drawing box (right)
      - user submits strokes -> grade_strokes(strokes, kanji)
      - must get grade==0 to proceed (otherwise forced retry)
      - user can restart canonical animation and clear user drawing
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # self._cards: list[KanjiCard] = []
        self._cards: Optional[Iterator[KanjiCard]] = None
        #self._idx: int = -1
        self._current: Optional[KanjiCard] = None

        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(12)

        self.stack = QtWidgets.QStackedWidget(self)
        root.addWidget(self.stack, 1)

        # -----------------------
        # Main learn page
        # -----------------------
        self.q_page = QtWidgets.QWidget(self.stack)
        q_root = QtWidgets.QVBoxLayout(self.q_page)
        q_root.setSpacing(12)

        # Header: kanji + readings/meaning
        self.kanji_label = QtWidgets.QLabel("—", self.q_page)
        self.kanji_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        f = self.kanji_label.font()
        f.setPointSize(64)
        f.setBold(True)
        self.kanji_label.setFont(f)

        self.reading_label = QtWidgets.QLabel("", self.q_page)
        self.reading_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.reading_label.setWordWrap(True)

        self.meaning_label = QtWidgets.QLabel("", self.q_page)
        self.meaning_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.meaning_label.setWordWrap(True)

        self.q_status = QtWidgets.QLabel("Press Start to begin.", self.q_page)
        self.q_status.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        q_root.addWidget(self.kanji_label)
        q_root.addWidget(self.reading_label)
        q_root.addWidget(self.meaning_label)
        q_root.addWidget(self.q_status)

        # Two-panel area: canonical (left) + user drawing (right)
        panels = QtWidgets.QHBoxLayout()
        panels.setSpacing(12)

        # Left: canonical drawing (animated)
        left_box = QtWidgets.QGroupBox("Correct drawing", self.q_page)
        left_layout = QtWidgets.QVBoxLayout(left_box)
        left_layout.setSpacing(8)

        self.canonical_display = DrawingDisplay(parent=left_box, width=320, height=320)
        left_layout.addWidget(self.canonical_display, 1)

        self.replay_btn = QtWidgets.QPushButton("Replay animation", left_box)
        self.replay_btn.clicked.connect(self._replay_canonical)
        left_layout.addWidget(self.replay_btn)

        # Right: user drawing input
        right_box = QtWidgets.QGroupBox("Your drawing", self.q_page)
        right_layout = QtWidgets.QVBoxLayout(right_box)
        right_layout.setSpacing(8)

        self.drawing = CharacterDrawing(
            parent=right_box,
            on_submitted=self._on_submitted,
            on_cleared=self._on_cleared,
        )
        right_layout.addWidget(self.drawing, 1)

        self.clear_user_btn = QtWidgets.QPushButton("Clear", right_box)
        self.clear_user_btn.clicked.connect(self.drawing.force_clear)
        right_layout.addWidget(self.clear_user_btn)

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
        # Empty / Done page
        # -----------------------
        self.done_page = QtWidgets.QLabel("Nothing to learn.", self.stack)
        self.done_page.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.stack.addWidget(self.done_page)
        self.stack.addWidget(self.q_page)
        self.stack.setCurrentWidget(self.done_page)

        # Defaults for status label (font/palette reset)
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
        if self._cards is None:  # prevent restarting on every show
            self.start()

    @QtCore.pyqtSlot()
    def start(self) -> None:
        if not self._cards:
            self._cards = query_learnable_kanji_cards()

        self._idx = -1
        self.next_card()

    @QtCore.pyqtSlot()
    def restart(self) -> None:
        self._cards = None
        self._current = None

        self.drawing.force_clear()
        self.canonical_display.set_strokes([])
        self.canonical_display.stop()

        self.kanji_label.setText("—")
        self.reading_label.setText("")
        self.meaning_label.setText("")
        self._reset_status_style()
        self.q_status.setText("Press Start to begin.")
        self.stack.setCurrentWidget(self.done_page)



    @QtCore.pyqtSlot()
    def next_card(self) -> None:
        self._reset_status_style()

        if self._cards is None:
            self.done_page.setText("✓ No more learnable kanji cards.")
            self.stack.setCurrentWidget(self.done_page)
            return

        try:
            self._current = next(self._cards)
        except StopIteration:
            self._current = None
            self._cards = None
            self.done_page.setText("✓ No more learnable kanji cards.")
            self.stack.setCurrentWidget(self.done_page)
            return

        self.drawing.force_clear()

        self.kanji_label.setText(self._current.kanji)

        oy = self._current.on_yomi or ""
        ky = self._current.kun_yomi or ""
        if oy and ky:
            self.reading_label.setText(f"On: {oy}   Kun: {ky}")
        elif oy:
            self.reading_label.setText(f"On: {oy}")
        elif ky:
            self.reading_label.setText(f"Kun: {ky}")
        else:
            self.reading_label.setText("")

        self.meaning_label.setText(self._current.meaning or "")
        self.q_status.setText("Watch the correct drawing, then copy it and click Submit.")

        d = self._current.drawing
        if d is not None and d.strokes:
            self.canonical_display.set_strokes(d.strokes)
            self.canonical_display.restart()
        else:
            self.canonical_display.set_strokes([])
            self.canonical_display.stop()
            self.q_status.setText("No canonical drawing found for this card. Draw anyway and Submit.")

        self.stack.setCurrentWidget(self.q_page)



    # @QtCore.pyqtSlot()
    # def next_card(self) -> None:
    #     self._reset_status_style()

    #     self._idx += 1
    #     if self._idx >= len(self._cards):
    #         self._current = None
    #         self.done_page.setText("✓ No more learnable kanji cards.")
    #         self.stack.setCurrentWidget(self.done_page)
    #         return

    #     self._current = self._cards[self._idx]
    #     self.drawing.force_clear()

    #     self.kanji_label.setText(self._current.kanji)

    #     oy = self._current.on_yomi or ""
    #     ky = self._current.kun_yomi or ""
    #     if oy and ky:
    #         self.reading_label.setText(f"On: {oy}   Kun: {ky}")
    #     elif oy:
    #         self.reading_label.setText(f"On: {oy}")
    #     elif ky:
    #         self.reading_label.setText(f"Kun: {ky}")
    #     else:
    #         self.reading_label.setText("")

    #     self.meaning_label.setText(self._current.meaning or "")

    #     self.q_status.setText("Watch the correct drawing, then copy it and click Submit.")

    #     # Load + play canonical drawing (must exist in DB for this card)
    #     d = self._current.drawing
    #     if d is not None and d.strokes:
    #         self.canonical_display.set_strokes(d.strokes)
    #         self.canonical_display.restart()
    #     else:
    #         self.canonical_display.set_strokes([])
    #         self.canonical_display.stop()
    #         self.q_status.setText("No canonical drawing found for this card. Draw anyway and Submit.")

    #     self.stack.setCurrentWidget(self.q_page)

    # -----------------------
    # Canonical controls
    # -----------------------

    def _replay_canonical(self) -> None:
        try:
            self.canonical_display.restart()
        except Exception:
            pass

    # -----------------------
    # Drawing callbacks
    # -----------------------

    def _on_cleared(self) -> None:
        if self._current is None:
            return
        self._reset_status_style()
        self.q_status.setText("Cleared. Try again, then Submit.")

    def _on_submitted(self, strokes: list[list[float]]) -> None:
        if self._current is None:
            return
        if not strokes:
            self._reset_status_style()
            self.q_status.setText("No strokes captured — draw something first.")
            return

        glyph = self._current.kanji
        g = grade_strokes(strokes, glyph)

        # Styling for feedback
        font = self.q_status.font()
        font.setPointSize(24)
        font.setBold(True)
        self.q_status.setFont(font)

        pal = self.q_status.palette()

        # 0 = correct (green), 1 = close (yellow), 2 = incorrect (red)
        if g == 0:
            pal.setColor(QPalette.ColorRole.WindowText, QColorConstants.Green)
            self.q_status.setText("Correct — moving on!")
            self.q_status.setPalette(pal)

            # Mark learned (do NOT touch drawing_id; canonical stays canonical)
            self._current.card.study_id = 1
            self._current.sync()

            self.next_card()
            return

        if g == 1:
            pal.setColor(QPalette.ColorRole.WindowText, QColorConstants.Yellow)
            self.q_status.setText("Close — try again.")
        else:
            pal.setColor(QPalette.ColorRole.WindowText, QColorConstants.Red)
            self.q_status.setText("Incorrect — try again.")

        self.q_status.setPalette(pal)

        # Force retry: clear user strokes; stay on same card
        self.drawing.force_clear()


# Backwards compat with your older name
LearnKanjiWidget = LearnKanjiPage
