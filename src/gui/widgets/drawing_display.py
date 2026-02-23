from typing import Optional
from itertools import cycle
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QColor, QImage, QPen, QPainter, QPaintEvent, QResizeEvent
from PyQt6.QtWidgets import QWidget
from logic.drawing_utils import normalize_strokes



class DrawingDisplay(QWidget):
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
                 width=300,
                 height=300,
                 milisec_per_point = 10):
        super().__init__(parent)

        self.setMinimumSize(width, height)
        
        # Make pen for drawing
        self._pen = QPen(
            Qt.GlobalColor.black,
            3,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin)
        self._pen.setColor(next(self.pen_colors))
        
        # Create surface for drawing
        self._image = QImage(width,height,QImage.Format.Format_ARGB32_Premultiplied)
        self._image.fill(self.palette().color(self.backgroundRole()))

        # Initialize stroke information
        self._raw_strokes: list[list[float]] | None = None
        self._point_strokes: list[list[QPointF]] = []
        self._current_stroke_index: int = 0
        self._current_stroke_point_index: int = 1
        self._current_stroke_point_count: int = 0
        
        # Initialize timer
        self._milisec_per_point = milisec_per_point
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        


    def _tick(self) -> None:
        if self._point_strokes is None or len(self._point_strokes) == 0:
            self.stop()
            return

        last_point = None
        this_point = None
        this_stroke = self._point_strokes[self._current_stroke_index]
        
        last_point = this_stroke[self._current_stroke_point_index - 1]
        this_point = this_stroke[self._current_stroke_point_index]

        p = QPainter(self._image)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(self._pen)
        p.drawLine(last_point, this_point)
        p.end()
        
        self.update()
        self.setup_next_point()



    def setup_next_point(self):
        next_stroke_point_ind = self._current_stroke_point_index + 1

        if next_stroke_point_ind >= self._current_stroke_point_count:
            if self._current_stroke_index + 1 >= len(self._point_strokes):
                self._current_stroke_point_index = 1
                self._current_stroke_point_count = len(self._point_strokes[0])
                self._current_stroke_index = 0
                self.stop() # terminate the timer loop, having completed the drawing
            else:
                self._current_stroke_index += 1
                self._current_stroke_point_index = 1
                self._current_stroke_point_count = len(self._point_strokes[self._current_stroke_index])
                self._pen.setColor(next(self.pen_colors)) # Change the pen color each stroke
        else:
            self._current_stroke_point_index = next_stroke_point_ind
                
        

    def resizeEvent(self, a0: Optional[QResizeEvent]) -> None:
        super().resizeEvent(a0)
        # Create new backing store at new size
        new_img = QImage(self.size(), QImage.Format.Format_ARGB32_Premultiplied)
        new_img.fill(self.palette().color(self.backgroundRole()))
        self._image = new_img

        # Re-map strokes to new size then redraw
        if self._raw_strokes is not None:
            self.set_strokes(self._raw_strokes)
            self.set_strokes(self._raw_strokes)
            self.restart()
        else:
            self.update()



    # def sizeHint(self) -> QSize:
    #     return self.minimumSizeHint()



    def paintEvent(self, a0: Optional[QPaintEvent]) -> None:
        p = QPainter(self)
        p.drawImage(0, 0, self._image)
        p.end()
        


    def stop(self) -> None:
        self._timer.stop()



    def resume(self) -> None:
        self._timer.start(self._milisec_per_point)



    def restart(self) -> None:
        self._image.fill(self.palette().color(self.backgroundRole()))
        self._current_stroke_index = 0
        self._current_stroke_point_index = 1
        self._current_stroke_point_count = len(self._point_strokes[self._current_stroke_index])
        self.update()
        self.resume()


    def set_strokes(self, strokes: list[list[float]]):
        # assert that the strokes are well formed
        for s in strokes:
            l = len(s)
            # There same number x and y value
            if l % 2 != 0:
                raise ValueError('Invalid strokes: not same number of x y values')
            # There are atleast 2 points
            if l // 2 < 2:
                raise ValueError('Invalid strokes: stoke has less than two points')
        normalized = normalize_strokes(strokes,
                                       width=float(self._image.width()),
                                       height=float(self._image.height()))
        # Assign values
        self._raw_strokes = strokes
        self._current_stroke_index = 0
        self._current_stroke_point_index = 1
        self._point_strokes = [[QPointF(p[0], p[1])
                                for p in zip(s[::2], s[1::2])]
                                    for s in normalized]
        self._current_stroke_point_count = len(self._point_strokes[self._current_stroke_index])
