import math
from typing import Callable, Optional
from itertools import cycle
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QPoint, QRect, QSize
from PyQt6.QtGui import QPainter, QPen, QImage, QColor, QMouseEvent, QPaintEvent

from PyQt6.QtWidgets import (QWidget,
                             QGridLayout,
                             QPushButton,
                             QFrame,
                             QHBoxLayout,
                             QVBoxLayout,
                             QSizePolicy,
                             QGridLayout)












class DrawingSurface(QWidget):

    pen_colors = cycle([
        QColor("#1f77b4"), QColor("#ff7f0e"),
        QColor("#2ca02c"), QColor("#d62728"),
        QColor("#9467bd"), QColor("#8c564b"),
        QColor("#e377c2"), QColor("#7f7f7f"),
        QColor("#bcbd22"), QColor("#17becf"),
        QColor("#393b79"), QColor("#637939"),
        QColor("#8c6d31"), QColor("#843c39"),
        QColor("#7b4173"), QColor("#3182bd"),
        QColor("#e6550d"), QColor("#31a354"),
        QColor("#756bb1"), QColor("#636363"),
        QColor("#9c9ede"), QColor("#cedb9c"),
        QColor("#e7ba52"), QColor("#ad494a"),
        QColor("#a55194"), QColor("#6baed6"),
        QColor("#fd8d3c"), QColor("#74c476"),
        QColor("#9e9ac8"), QColor("#bdbdbd"),
        QColor("#b5cf6b"), QColor("#17becf")])
    

    def __init__(self,
                 parent=None,
                 min_w: int = 100,
                 min_h: int = 100):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(min_w,min_h)
        self.strokes = []
        self.current_stroke = None

        self.pen = QPen(
            Qt.GlobalColor.black,
            3,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin)

        # backing store we draw onto (safer than QPixmap for offscreen)
        self.image = QImage(min_w, min_h, QImage.Format.Format_ARGB32_Premultiplied)
        self.image.fill(self.palette().color(self.backgroundRole()))
        self.last_point: QPoint | None = None
        self.is_drawing = False
        #self.setFixedSize(fixed_x_size, fixed_y_size)

    # --- QWidget overrides ---
    def sizeHint(self):
        #return QSize(self.image.width(), self.image.height())
        return QSize(160,160)

    def paintEvent(self, a0: Optional[QPaintEvent]):
        _ = a0
        p = QPainter(self)                     # paint widget from backing image
        p.drawImage(0, 0, self.image)




    def resizeEvent(self, a0) -> None:
        assert a0
        new_w = max(1, a0.size().width())
        new_h = max(1, a0.size().height())

        old_w = self.image.width()
        old_h = self.image.height()

        if new_w == old_w and new_h == old_h:
            super().resizeEvent(a0)
            return

        # Create new backing store
        new_img = QImage(new_w, new_h, QImage.Format.Format_ARGB32_Premultiplied)
        new_img.fill(self.palette().color(self.backgroundRole()))

        # Scale existing pixels to the new image
        p = QPainter(new_img)
        try:
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            p.drawImage(0, 0, self.image.scaled(new_w, new_h))
        finally:
            p.end()

        # Scale stored stroke coordinates so they remain consistent with the new size
        if old_w > 0 and old_h > 0 and self.strokes:
            sx = new_w / old_w
            sy = new_h / old_h

            scaled_strokes: list[list[float]] = []
            for stroke in self.strokes:
                if not stroke:
                    scaled_strokes.append(stroke)
                    continue
                s2: list[float] = []
                # stroke is [x0, y0, x1, y1, ...]
                for i in range(0, len(stroke) - 1, 2):
                    x = stroke[i]
                    y = stroke[i + 1]
                    s2.append(x * sx)
                    s2.append(y * sy)
                scaled_strokes.append(s2)
            self.strokes = scaled_strokes

        self.image = new_img
        super().resizeEvent(a0)
    # --- Mouse handling: draw onto the QImage ---

    def mousePressEvent(self, a0: Optional[QMouseEvent]):
        if not a0:
            return
        if a0.button() == Qt.MouseButton.LeftButton:
            self.pen.setColor(next(self.pen_colors))
            self.is_drawing = True
            self.last_point = a0.position().toPoint()

    def mouseMoveEvent(self, a0):
        if not a0:
            return
        if self.is_drawing and (a0.buttons() & Qt.MouseButton.LeftButton):
            cur = a0.position().toPoint()       # QPoint (ints)
            p = QPainter(self.image)

            if self.current_stroke is None:
                self.current_stroke = []
            self.current_stroke.append(cur.x())
            self.current_stroke.append(cur.y())

            if self.last_point is not None:
                try:
                    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                    p.setPen(self.pen)
                    p.drawLine(self.last_point, cur) # QPoint,QPoint overload (safe)
                finally:
                    p.end()
                # minimal repaint
                dirty = QRect(self.last_point, cur).normalized().adjusted(-4, -4, 4, 4)
                self.update(dirty)
            self.last_point = cur

    def mouseReleaseEvent(self, a0: Optional[QMouseEvent]):
        if not a0:
            return
        
        self.strokes.append(self.current_stroke)
        self.current_stroke = None

        print(self.strokes)

        if a0.button() == Qt.MouseButton.LeftButton:
            self.is_drawing = False
            self.last_point = None

    # --- optional public API ---

    def clear(self):
        self.image.fill(self.palette().color(self.backgroundRole()))
        self.is_drawing = False
        self.last_point = None
        self.strokes = []
        self.current_stroke = None
        self.update()




#class CharacterDrawing(QWidget):
class CharacterDrawing(QFrame):
    cleared = pyqtSignal()       # must be class attribute
    submitted = pyqtSignal(list) # must be class attribute
    
    def __init__(self,
                 parent = None,
                 on_cleared: Optional[Callable[[], None]] = None,
                 on_submitted: Optional[Callable[[list[list[float]]], None]] = None):
        super().__init__(parent)

        layout = QGridLayout()
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setSpacing(8)
        self.setLayout(layout)

        self.drawing_surface = DrawingSurface(parent=self)
        layout.addWidget(self.drawing_surface, 0, 0, 1, 2)

        clear_button = QPushButton('Clear', parent=self)
        clear_button.clicked.connect(self._handle_clear_clicked)
        layout.addWidget(clear_button, 1, 0, 1, 1)

        submit_button = QPushButton('Submit', parent=self)
        submit_button.clicked.connect(self._handle_submit_clicked)
        layout.addWidget(submit_button, 1, 1, 1, 1)

        if on_cleared is not None:
            self.cleared.connect(on_cleared)
        if on_submitted is not None:
            self.submitted.connect(on_submitted)


    def force_clear(self) -> None:
        self.drawing_surface.clear()


    @pyqtSlot()
    def _handle_clear_clicked(self) -> None:
        self.drawing_surface.clear()
        self.cleared.emit()


    @pyqtSlot()
    def _handle_submit_clicked(self) -> None:
        self.submitted.emit(self.drawing_surface.strokes)













class MultiCharacterDrawing(QFrame):
    """
    Multiple side-by-side DrawingSurface widgets, each in its own framed box.

    Public interface mirrors CharacterDrawing:
        - cleared (signal)
        - submitted (signal)
        - force_clear()

    Additional API:
        - set_count(n)
        - get_strokes() -> list[list[list[float]]]
    """

    cleared = pyqtSignal()
    submitted = pyqtSignal(list)  # list[list[list[float]]]

    def __init__(
        self,
        n: int = 1,
        parent=None,
        on_cleared: Optional[Callable[[], None]] = None,
        on_submitted: Optional[Callable[[list[list[list[float]]]], None]] = None,
    ):
        super().__init__(parent)

        # Store both the frames (for deletion) and the drawing surfaces (for strokes)
        self._frames: list[QFrame] = []
        self._surfaces: list[DrawingSurface] = []

        # --- Layout ---
        root = QGridLayout()
        root.setColumnStretch(0, 1)
        root.setColumnStretch(1, 1)
        root.setSpacing(8)
        self.setLayout(root)

        # Container for drawing row
        self._surface_container = QWidget(self)
        self._surface_layout = QHBoxLayout(self._surface_container)
        self._surface_layout.setSpacing(0)  # important: borders touch
        self._surface_layout.setContentsMargins(0, 0, 0, 0)

        root.addWidget(self._surface_container, 0, 0, 1, 2)

        # Buttons
        clear_button = QPushButton("Clear", parent=self)
        clear_button.clicked.connect(self._handle_clear_clicked)
        root.addWidget(clear_button, 1, 0)

        submit_button = QPushButton("Submit", parent=self)
        submit_button.clicked.connect(self._handle_submit_clicked)
        root.addWidget(submit_button, 1, 1)

        if on_cleared is not None:
            self.cleared.connect(on_cleared)
        if on_submitted is not None:
            self.submitted.connect(on_submitted)

        self.set_count(n)

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    def set_count(self, n: int) -> None:
        """
        Dynamically set number of drawing widgets.
        Existing drawings are destroyed.
        """
        if n <= 0:
            raise ValueError("set_count(n): n must be >= 1")

        # Delete old frames (surfaces are children of frames, so they go too)
        for f in self._frames:
            self._surface_layout.removeWidget(f)
            f.deleteLater()

        self._frames.clear()
        self._surfaces.clear()

        # Build new framed boxes
        for _ in range(n):
            frame = QFrame(parent=self._surface_container)
            frame.setFrameShape(QFrame.Shape.Box)
            frame.setLineWidth(2)
            frame.setMidLineWidth(0)

            # Tight layout inside the frame so the DrawingSurface fills it
            inner = QVBoxLayout(frame)
            inner.setContentsMargins(0, 0, 0, 0)
            inner.setSpacing(0)

            surface = DrawingSurface(parent=frame)
            inner.addWidget(surface, 1)

            self._surface_layout.addWidget(frame, 1)
            self._frames.append(frame)
            self._surfaces.append(surface)

        self.updateGeometry()

    def force_clear(self) -> None:
        """Clear all sub-drawings (does NOT emit cleared)."""
        for s in self._surfaces:
            s.clear()

    def get_strokes(self) -> list[list[list[float]]]:
        """Returns strokes for each sub-surface (left-to-right)."""
        return [s.strokes for s in self._surfaces]

    # ----------------------------------------------------------
    # Button handlers
    # ----------------------------------------------------------

    @pyqtSlot()
    def _handle_clear_clicked(self) -> None:
        self.force_clear()
        self.cleared.emit()

    @pyqtSlot()
    def _handle_submit_clicked(self) -> None:
        self.submitted.emit(self.get_strokes())







class _SquareCell(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(32, 32)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, a0: int) -> int:
        return a0

    def sizeHint(self) -> QSize:
        return QSize(160, 160)





class GenkouyoushiWidgets(QFrame):
    """
    Genkō yōshi style multi-character drawing widget.

    Layout rules:
      - Start at top-right
      - Fill downward (row 0 -> row_cap-1)
      - Wrap to next column to the LEFT
        (i.e., next rightmost column after finishing the current one)

    Public interface mirrors MultiCharacterDrawing:
      - cleared (signal)
      - submitted (signal)
      - force_clear()
      - get_strokes() -> list[list[list[float]]]
      - set_count(n)

    Additional API:
      - set_row_cap(n)
    """

    cleared = pyqtSignal()
    submitted = pyqtSignal(list)  # list[list[list[float]]]

    def __init__(
        self,
        count: int = 1,
        row_cap: int = 10,
        parent=None,
        on_cleared: Optional[Callable[[], None]] = None,
        on_submitted: Optional[Callable[[list[list[list[float]]]], None]] = None,
    ):
        super().__init__(parent)

        if row_cap <= 0:
            raise ValueError("row_cap must be >= 1")
        if count <= 0:
            raise ValueError("count must be >= 1")

        self._count = int(count)
        self._row_cap = int(row_cap)

        self._frames: list[QFrame] = []
        self._surfaces: list[DrawingSurface] = []

        # --- Outer layout: grid (drawing area) + button row ---
        root = QGridLayout(self)
        root.setRowStretch(0,1)
        root.setRowStretch(1,0)
        root.setSpacing(8)
        self.setLayout(root)

        # Drawing-area container
        self._grid_container = QWidget(self)
        self._grid_container.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        self._grid = QGridLayout(self._grid_container)
        self._grid.setSpacing(0)              # borders touch -> clear dividers
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid_container.setLayout(self._grid)

        root.addWidget(self._grid_container, 0, 0, 1, 2)

        # Buttons
        clear_button = QPushButton("Clear", self)
        clear_button.clicked.connect(self._handle_clear_clicked)
        root.addWidget(clear_button, 1, 0)

        submit_button = QPushButton("Submit", self)
        submit_button.clicked.connect(self._handle_submit_clicked)
        root.addWidget(submit_button, 1, 1)

        if on_cleared is not None:
            self.cleared.connect(on_cleared)
        if on_submitted is not None:
            self.submitted.connect(on_submitted)

        self._rebuild_cells()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_count(self, n: int) -> None:
        """Set the number of character cells."""
        if n <= 0:
            raise ValueError("set_count(n): n must be >= 1")
        self._count = int(n)
        self._rebuild_cells()

    def set_row_cap(self, n: int) -> None:
        """
        Set the maximum number of rows before wrapping to the next column (left).
        """
        if n <= 0:
            raise ValueError("set_row_cap(n): n must be >= 1")
        self._row_cap = int(n)
        self._rebuild_cells()

    def force_clear(self) -> None:
        """Clear all drawings (does NOT emit cleared)."""
        for s in self._surfaces:
            s.clear()

    def get_strokes(self) -> list[list[list[float]]]:
        """
        Returns strokes in writing order:
          top-right going down, then next column to the left, etc.
        Outer length == count.
        """
        return [s.strokes for s in self._surfaces]

    # ------------------------------------------------------------------
    # Internal: (re)build the genkou layout
    # ------------------------------------------------------------------

    def _clear_layout(self) -> None:
        # remove widgets from grid; delete frames (which own surfaces)
        for f in self._frames:
            self._grid.removeWidget(f)
            f.deleteLater()
        self._frames.clear()
        self._surfaces.clear()

        # also clear any leftover row/col stretch settings
        # (QGridLayout doesn't offer "clear stretches", but rebuild handles it)

    # def _rebuild_cells(self) -> None:
    #     self._clear_layout()

    #     count = self._count
    #     row_cap = self._row_cap

    #     cols = max(1, math.ceil(count / row_cap))

    #     # Ensure grid columns expand nicely
    #     for c in range(cols):
    #         self._grid.setColumnStretch(c, 1)
    #     for r in range(row_cap):
    #         self._grid.setRowStretch(r, 1)

    #     # Create cells in logical writing order index i:
    #     #   col = i // row_cap (0 is rightmost logical column)
    #     #   row = i % row_cap
    #     # Map logical column 0 -> grid column (cols-1), so it appears on the right.
    #     for i in range(count):
    #         logical_col = i // row_cap
    #         row = i % row_cap
    #         grid_col = (cols - 1) - logical_col  # make logical col 0 the rightmost

    #         frame = QFrame(self._grid_container)
    #         frame.setFrameShape(QFrame.Shape.Box)
    #         frame.setLineWidth(2)
    #         frame.setMidLineWidth(0)

    #         inner = QVBoxLayout(frame)
    #         inner.setContentsMargins(0, 0, 0, 0)
    #         inner.setSpacing(0)

    #         surface = DrawingSurface(parent=frame)
    #         inner.addWidget(surface, 1)

    #         self._grid.addWidget(frame, row, grid_col)

    #         self._frames.append(frame)
    #         self._surfaces.append(surface)

    #     self.updateGeometry()

# inside GenkouyoushiWidgets._rebuild_cells()
    def _rebuild_cells(self) -> None:
        self._clear_layout()

        count = self._count
        row_cap = self._row_cap
        cols = max(1, math.ceil(count / row_cap))

        self._grid.setSpacing(0)
        self._grid.setContentsMargins(0, 0, 0, 0)

        # (keep your cols/rows math)
        for c in range(cols):
            self._grid.setColumnStretch(c, 1)
        for r in range(row_cap):
            self._grid.setRowStretch(r, 1)

        for i in range(count):
            logical_col = i // row_cap
            row = i % row_cap
            grid_col = (cols - 1) - logical_col

            frame = _SquareCell(parent=self._grid_container)
            frame.setFrameShape(QFrame.Shape.Box)
            frame.setLineWidth(2)

            # new
            frame.setMinimumSize(120, 120)
            frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            inner = QVBoxLayout(frame)
            inner.setContentsMargins(0, 0, 0, 0)
            inner.setSpacing(0)

            surface = DrawingSurface(parent=frame)
            surface.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            inner.addWidget(surface, 1)

            self._grid.addWidget(frame, row, grid_col)
            self._frames.append(frame)
            self._surfaces.append(surface)

        self._grid.invalidate()
        self._grid_container.updateGeometry()
        self.updateGeometry()
    
    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    @pyqtSlot()
    def _handle_clear_clicked(self) -> None:
        self.force_clear()
        self.cleared.emit()

    @pyqtSlot()
    def _handle_submit_clicked(self) -> None:
        self.submitted.emit(self.get_strokes())
