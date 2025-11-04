from typing import Callable, Optional
from itertools import cycle
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QPoint, QRect
from PyQt6.QtGui import QPainter, QPen, QImage, QColor
from PyQt6.QtWidgets import QWidget, QGridLayout, QPushButton


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
    
    strokes = []
    current_stroke = None

    def __init__(self, parent=None):
        super().__init__(parent)

        self.pen = QPen(
            Qt.GlobalColor.black,
            3,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin)

        # backing store we draw onto (safer than QPixmap for offscreen)
        self.image = QImage(900, 600, QImage.Format.Format_ARGB32_Premultiplied)
        self.image.fill(self.palette().color(self.backgroundRole()))
        self.last_point: QPoint | None = None
        self.is_drawing = False
        #self.setFixedSize(fixed_x_size, fixed_y_size)

    # --- QWidget overrides ---
    def sizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(self.image.width(), self.image.height())

    def paintEvent(self, ev):
        p = QPainter(self)                     # paint widget from backing image
        p.drawImage(0, 0, self.image)

    
    # --- Mouse handling: draw onto the QImage ---
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.pen.setColor(next(self.pen_colors))
            self.is_drawing = True
            self.last_point = e.position().toPoint()

    def mouseMoveEvent(self, e):
        if self.is_drawing and (e.buttons() & Qt.MouseButton.LeftButton):
            cur = e.position().toPoint()       # QPoint (ints)
            p = QPainter(self.image)

            if self.current_stroke is None:
                self.current_stroke = []
            self.current_stroke.append(cur.x())
            self.current_stroke.append(cur.y())

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

    def mouseReleaseEvent(self, e):
        self.strokes.append(self.current_stroke)
        self.current_stroke = None

        print(self.strokes)

        if e.button() == Qt.MouseButton.LeftButton:
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


class CharacterDrawing(QWidget):

    drawing_surface: DrawingSurface = None

    cleared = pyqtSignal()
    submitted = pyqtSignal(list) 
    
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
