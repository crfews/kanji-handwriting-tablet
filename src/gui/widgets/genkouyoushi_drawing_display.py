from __future__ import annotations

import math
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from data.drawing import Drawing
from gui.widgets.drawing_display import DrawingDisplay


class GenkouyoushiDrawingDisplay(QFrame):
    """
    Displays a string of glyphs using a genkō-yōshi layout:
      - start at top-right
      - fill downward
      - wrap to next column on the left after row_cap cells

    One shared set of buttons:
      - Restart: restarts all animations
      - Redraw: re-fetch strokes from DB (Drawing.by_glyph) and restart

    Notes:
      - For each glyph, we pick one Drawing from Drawing.by_glyph(glyph).
        Currently: choose the smallest drawing id (deterministic).
    """

    def __init__(
        self,
        text: str = "",
        row_cap: int = 10,
        parent=None,
        cell_width: int = 120,
        cell_height: int = 120,
        milisec_per_point: int = 10,
    ):
        super().__init__(parent)

        if row_cap <= 0:
            raise ValueError("row_cap must be >= 1")

        self._text = text
        self._row_cap = int(row_cap)
        self._cell_w = int(cell_width)
        self._cell_h = int(cell_height)
        self._ms_per_point = int(milisec_per_point)

        self._frames: list[QFrame] = []
        self._displays: list[DrawingDisplay] = []
        self._glyphs: list[str] = []
        self._progress_value: int = 0

        # Outer layout
        root = QGridLayout(self)
        root.setSpacing(8)
        self.setLayout(root)

        # Grid container
        self._grid_container = QWidget(self)
        self._grid = QGridLayout(self._grid_container)
        self._grid.setSpacing(0)              # borders touch -> visible dividers
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid_container.setLayout(self._grid)
        root.addWidget(self._grid_container, 0, 0, 1, 2)

        # Representation slider
        rep_row = QHBoxLayout()
        rep_row.addWidget(QLabel("Animation Slider", self))
        self._variant_slider = QSlider(self)
        self._variant_slider.setOrientation(Qt.Orientation.Horizontal)
        self._variant_slider.setRange(0, 100)
        self._variant_slider.setEnabled(True)
        self._variant_slider.valueChanged.connect(self._on_variant_changed)
        rep_row.addWidget(self._variant_slider, 1)
        self._variant_label = QLabel("0%", self)
        rep_row.addWidget(self._variant_label)
        root.addLayout(rep_row, 1, 0, 1, 2)

        # Buttons
        self._restart_btn = QPushButton("Restart animation", self)
        self._restart_btn.clicked.connect(self.restart)
        root.addWidget(self._restart_btn, 2, 0)

        self._redraw_btn = QPushButton("Redraw (reload from DB)", self)
        self._redraw_btn.clicked.connect(self.redraw)
        root.addWidget(self._redraw_btn, 2, 1)

        # Build initial UI
        self.set_text(text)

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def set_text(self, text: str) -> None:
        """Set the displayed text and rebuild the grid."""
        self._text = text or ""
        self._glyphs = list(self._text)
        self._rebuild_grid()
        self._sync_variant_slider()
        self.redraw()  # load strokes for current glyphs

    def set_row_cap(self, n: int) -> None:
        """Change wrap height and rebuild."""
        if n <= 0:
            raise ValueError("set_row_cap(n): n must be >= 1")
        self._row_cap = int(n)
        self._rebuild_grid()
        # keep existing glyphs, reload strokes into the new displays
        self._sync_variant_slider()
        self.redraw()

    def set_progress_value(self, value: int) -> None:
        """Set scrubber progress in percent [0..100]."""
        self._progress_value = max(0, min(100, int(value)))
        if self._variant_slider.value() != self._progress_value:
            self._variant_slider.blockSignals(True)
            self._variant_slider.setValue(self._progress_value)
            self._variant_slider.blockSignals(False)
        self._sync_variant_label()
        self._apply_progress()

    def _sync_variant_slider(self) -> None:
        self._variant_slider.blockSignals(True)
        self._variant_slider.setRange(0, 100)
        self._variant_slider.setValue(self._progress_value)
        self._variant_slider.blockSignals(False)
        self._variant_slider.setEnabled(True)
        self._sync_variant_label()

    def _sync_variant_label(self) -> None:
        self._variant_label.setText(f"{self._progress_value}%")

    def _apply_progress(self) -> None:
        p = self._progress_value / 100.0
        for disp in self._displays:
            disp.set_progress(p)

    def _on_variant_changed(self, value: int) -> None:
        self._progress_value = max(0, min(100, int(value)))
        self._sync_variant_label()
        self._apply_progress()

    @pyqtSlot()
    def restart(self) -> None:
        """Restart all animations (does not re-fetch DB)."""
        for d in self._displays:
            try:
                # If it has no strokes, restart() would crash (it assumes at least 1 stroke)
                # so guard by checking internal state indirectly: just try.
                d.restart()
            except Exception:
                # empty/no-strokes case; ignore
                pass

    @pyqtSlot()
    def redraw(self) -> None:
        """
        Re-fetch strokes for each glyph from DB and restart the animations.
        Uses Drawing.by_glyph(g).
        """
        for glyph, disp in zip(self._glyphs, self._displays, strict=False):
            strokes: list[list[float]] = []

            drawings = Drawing.by_glyph(glyph)
            if drawings:
                # deterministic choice: smallest id
                d_id = min(drawings.keys())
                strokes = drawings[d_id].strokes

            if strokes:
                disp.set_strokes(strokes)
                disp.set_progress(self._progress_value / 100.0)
            else:
                # No drawing found: clear the display
                disp.stop()

    # ---------------------------------------------------------------------
    # Internal: grid rebuild
    # ---------------------------------------------------------------------

    def _clear_grid(self) -> None:
        for f in self._frames:
            self._grid.removeWidget(f)
            f.deleteLater()
        self._frames.clear()
        self._displays.clear()

    def _rebuild_grid(self) -> None:
        self._clear_grid()

        count = len(self._glyphs)
        if count <= 0:
            self.updateGeometry()
            return

        row_cap = self._row_cap
        cols = max(1, math.ceil(count / row_cap))

        for c in range(cols):
            self._grid.setColumnStretch(c, 1)
        for r in range(row_cap):
            self._grid.setRowStretch(r, 1)

        for i in range(count):
            logical_col = i // row_cap          # 0 = rightmost logical column
            row = i % row_cap
            grid_col = (cols - 1) - logical_col # place logical col 0 on the right

            frame = QFrame(self._grid_container)
            frame.setFrameShape(QFrame.Shape.Box)
            frame.setLineWidth(2)

            inner = QVBoxLayout(frame)
            inner.setContentsMargins(0, 0, 0, 0)
            inner.setSpacing(0)

            disp = DrawingDisplay(
                parent=frame,
                width=self._cell_w,
                height=self._cell_h,
                milisec_per_point=self._ms_per_point,
            )
            inner.addWidget(disp, 1)

            self._grid.addWidget(frame, row, grid_col)
            self._frames.append(frame)
            self._displays.append(disp)

        self.updateGeometry()
