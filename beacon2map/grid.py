#!/usr/bin/env python

import math
from PySide6.QtGui import QColor, QPainter, QPen

from PySide6.QtCore import QPropertyAnimation, QRectF
from PySide6.QtWidgets import QGraphicsObject

from utility import Extents


class Grid(QGraphicsObject):
    def __init__(self, map_extents: Extents = None):
        super().__init__()
        self.map_extents = map_extents

        self._extents = None
        self._major = None
        self._minor = None
        self._major_color = None
        self._minor_color = None
        self.calculate_extents()

        self.is_being_redrawn = False
        self.animation = QPropertyAnimation(self, b'opacity')
        self.animation.setDuration(150)
        self.animation.finished.connect(self._animation_finished)

    def calculate_extents(self) -> None:
        '''Calculate grid extents to encompass locations extents.'''
        self.extents = Extents(
            min_x=math.floor(self.map_extents.min_x/self.major) * self.major,
            max_x=math.ceil(self.map_extents.max_x/self.major) * self.major,
            min_y=math.floor(self.map_extents.min_y/self.major) * self.major,
            max_y=math.ceil(self.map_extents.max_y/self.major) * self.major
        )

    def draw_lines(self, painter: QPainter, step: int) -> None:
        ex = self.extents
        for x in range(ex.min_x, ex.max_x+1, step):
            painter.drawLine(x, ex.min_y, x, ex.max_y)
        for y in range(ex.min_y, ex.max_y+1, step):
            painter.drawLine(ex.min_x, y, ex.max_x, y)

    def paint(self, painter: QPainter, option, widget) -> None:
        painter.setPen(QPen(self.minor_color))
        self.draw_lines(painter, self.minor)
        painter.setPen(QPen(self.major_color))
        self.draw_lines(painter, self.major)

    def boundingRect(self) -> QRectF:
        '''boundingRect is the Grid's extents plus a margin equal to one major
        grid step on all four sides.
        '''
        return QRectF(
            self.extents.min_x - self.major,
            self.extents.min_y - self.major,
            self.width + self.major * 2,
            self.height + self.major * 2)

    def setVisible(self, visible: bool) -> None:
        '''Fade in/out animation. Cast the passed bool value as an integer for
        the target opacity values.'''
        if self.is_being_redrawn:
            return
        else:
            self.is_being_redrawn = True
            super().setVisible(True)
            self.animation.setStartValue(int(not visible))
            self.animation.setEndValue(int(visible))
            self.animation.start()

    def _animation_finished(self):
        '''We cast the opacity float value back to a bool.'''
        self.is_being_redrawn = False
        return super().setVisible(bool(self.opacity()))

    @property
    def map_extents(self):
        return self._map_extents or Extents(-500, 500, -500, 500, -500, 500)

    @map_extents.setter
    def map_extents(self, value: Extents):
        self._map_extents = value

    @property
    def width(self):
        return self.extents.max_x - self.extents.min_x

    @property
    def height(self):
        return self.extents.max_y - self.extents.min_y

    @property
    def major(self):
        return self._major or 100

    @major.setter
    def major(self, value: int):
        self._major = value
        self.calculate_extents()

    @property
    def minor(self):
        return self._minor or 20

    @minor.setter
    def minor(self, value: int):
        self._minor = value
        self.calculate_extents()

    @property
    def major_color(self):
        return self._major_color or QColor('white')

    @major_color.setter
    def major_color(self, value: QColor):
        self._major_color = value

    @property
    def minor_color(self):
        return self._minor_color or QColor('darkblue')

    @minor_color.setter
    def minor_color(self, value: QColor):
        self._minor_color = value

#
# Barebones test window for QGraphicsItem/QGraphicsObject 
#

if (__name__ == '__main__'):
    from PySide6.QtWidgets import QApplication
    from PySide6.QtWidgets import QGraphicsScene, QGraphicsView
    a = QApplication()
    s = QGraphicsScene()

    # Modify with required class
    i = Grid()
    s.addItem(i)
    s.addText('Grid Class')

    v = QGraphicsView(s)
    v.show()
    a.exec()
