from __future__ import annotations

from typing import Iterator, Optional
from datetime import date
import sqlalchemy as sqla
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt
from data import KanaCard, Drawing
from data.database import maybe_connection
from gui.widgets.writing_widgets import CharacterDrawing
# your stuff
# from data.queries import query_learnable_kana_cards
# from data import KanaCard
# from widgets.character_drawing import CharacterDrawing

# IMPORTANT FIX: DrawingSurface must use instance state (not class vars)
# In your DrawingSurface class, remove these class attributes:
#   strokes = []
#   current_stroke = None
# and instead set them in __init__:
#   self.strokes: list[list[float]] = []
#   self.current_stroke: list[float] | None = None


class LearnKanaWidget(QtWidgets.QWidget):
    """
    Minimal "learn session" driver:
      - iterates learnable KanaCards
      - shows one card
      - waits for drawing submission before advancing
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Session state
        self._it: Optional[Iterator[KanaCard]] = None
        self._current: Optional[KanaCard] = None
        self._submitted_for_current = False

        # --- UI ---
        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(12)

        # Top: card prompt / info
        self.kana_label = QtWidgets.QLabel("", self)
        self.kana_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        f = self.kana_label.font()
        f.setPointSize(64)
        f.setBold(True)
        self.kana_label.setFont(f)

        self.romaji_label = QtWidgets.QLabel("", self)
        self.romaji_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.status_label = QtWidgets.QLabel("", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        root.addWidget(self.kana_label)
        root.addWidget(self.romaji_label)
        root.addWidget(self.status_label)

        # Middle: drawing
        self.drawing = CharacterDrawing(
            parent=self,
            on_cleared=self._on_cleared,
            on_submitted=self._on_submitted,
        )
        root.addWidget(self.drawing, 1)

        # Bottom: session controls (optional but handy)
        btns = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("Start", self)
        self.start_btn.clicked.connect(self.start)

        self.skip_btn = QtWidgets.QPushButton("Skip", self)
        self.skip_btn.clicked.connect(self.next_card)

        self.restart_btn = QtWidgets.QPushButton("Restart", self)
        self.restart_btn.clicked.connect(self.restart)

        btns.addWidget(self.start_btn)
        btns.addWidget(self.skip_btn)
        btns.addWidget(self.restart_btn)
        root.addLayout(btns)

        self._set_idle()

    # ---------------------------
    # Session control
    # ---------------------------

    @QtCore.pyqtSlot()
    def start(self) -> None:
        if self._it is None:
            with maybe_connection(None) as con:
                from data.queries import query_learnable_kana_cards  # local import to avoid cycles
                self._it = iter(list(query_learnable_kana_cards(con)))
                                    
        self.next_card()

    @QtCore.pyqtSlot()
    def restart(self) -> None:
        self._it = None
        self._current = None
        self._submitted_for_current = False
        self.drawing.force_clear()
        self._set_idle()

    @QtCore.pyqtSlot()
    def next_card(self) -> None:
        if self._it is None:
            self.start()
            return

        try:
            self._current = next(self._it)
        except StopIteration:
            self._current = None
            self._set_done()
            return

        self._submitted_for_current = False
        self.drawing.force_clear()
        self._render_current()

    # ---------------------------
    # UI helpers
    # ---------------------------

    def _set_idle(self) -> None:
        self.kana_label.setText("—")
        self.romaji_label.setText("")
        self.status_label.setText("Press Start to begin.")

    def _set_done(self) -> None:
        self.kana_label.setText("✓")
        self.romaji_label.setText("")
        self.status_label.setText("No more learnable kana cards.")

    def _render_current(self) -> None:
        assert self._current is not None
        # adjust attribute names to your KanaCard API
        self.kana_label.setText(getattr(self._current, "kana", ""))
        self.romaji_label.setText(getattr(self._current, "romaji", "") or "")
        self.status_label.setText("Draw it, then click Submit.")

    # ---------------------------
    # Drawing callbacks
    # ---------------------------

    def _on_cleared(self) -> None:
        if self._current is None:
            return
        self._submitted_for_current = False
        self.status_label.setText("Cleared. Draw it again, then Submit.")

    def _on_submitted(self, strokes: list[list[float]]) -> None:
        """
        Called ONLY when the user submits a drawing.
        This is the "gate": we do not advance until this happens.
        """
        if self._current is None:
            return

        if not strokes:
            self.status_label.setText("No strokes captured — draw something first.")
            return

        self._submitted_for_current = True

        # Here is where you do something meaningful with (card, strokes):
        # - score handwriting
        # - save drawing to DB
        # - mark card studied
        #
        # For now we just print a useful summary.
        print(
            f"Submitted for kana={getattr(self._current, 'kana', '')!r}, "
            f"romaji={getattr(self._current, 'romaji', '')!r}, "
            f"strokes={len(strokes)}"
        )

        
        self._current.drawing = Drawing.create(strokes, self._current.kana)
        self._current.card.study_id = 1
        self._current.sync()
        
        # Advance to next card ONLY after successful submission
        self.next_card()
