#!/usr/bin/env python

"""
beacon2map creates a visual map based on marker locations read from a CSV file.
The markers hold names and descriptions and are based on
readings of distance, depth and bearing to a central reference beacon.

This app was designed as an exploration aid for the video game Subnautica.

Requirements: Qt6 and Pandas
"""

__author__ = "Tal Zana"
__copyright__ = "Copyright 2021"
__license__ = "GPL"
__version__ = "1.0"

import sys
import math

from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QColor, QFont, QPen, QBrush, QPolygon, QPainter
from PySide6.QtCore import Qt, QRectF, QPoint

from markerdata import MarkerData

FILENAME = 'sub-sample.csv'

MAJOR_GRID = 500
MINOR_GRID = 100

MAJOR_GRID_COLOR = QColor('dodgerblue')
MINOR_GRID_COLOR = QColor('mediumblue')
BACKGROUND_COLOR = QColor('darkblue')
MARKER_DONE_COLOR = QColor('slateblue')

INIT_SCALE = 0.75
WIN_WIDTH = 2560
WIN_HEIGHT = 1440

FONT_FAMILY = 'Helvetica'
FONT_SIZE = 16
FONT_BOLD = True

MARKERS = {
    'pod':         {'color': 'limegreen', 'shape': 'star'},
    'wreck':       {'color': 'bisque', 'shape': 'x'},
    'biome':       {'color': 'coral', 'shape': 'circle'},
    'interest':    {'color': 'gold', 'shape': 'triangle'},
    'alien':       {'color': 'orchid', 'shape': 'square'},
    'mur':         {'color': 'deepskyblue', 'shape': 'square'},
    'misc':        {'color': 'darkorange', 'shape': 'circle'}
    }

SHAPES = {
    'square': [(-4, -4), (4, -4), (4, 4), (-4, 4)],
    'triangle': [(0, -4), (4, 4), (-4, 4)],
    'star': [(-1, -1), (0, -5), (1, -1), (5, 4), (0, 1), (-5, 4), (-1, -1)],
    'x': [(0, -2), (3, -5), (5, -3), (2, 0), (5, 3),
          (3, 5), (0, 2), (-3, 5), (-5, 3), (-2, 0), (-5, -3), (-3, -5)]
    }


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.scene = MapScene(FILENAME)
        self.view = MapView(self.scene)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.view)


class MapMarker(QtWidgets.QGraphicsItem):
    def __init__(self, marker, label, depth, done):
        super().__init__()
        self.marker = marker
        self.label = label
        self.depth = depth
        self.done = done

        # Set Qt flags
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations)

        # Build QPolygon dictionary from SHAPES coordinates
        self.shapes = {}
        for k, v in SHAPES.items():
            self.shapes[k] = QPolygon([QPoint(*point)for point in SHAPES[k]])

        # Set marker color
        self.color = MARKER_DONE_COLOR if self.done else QColor(
            MARKERS[self.marker]['color'])

    def paint(self, painter, option, widget):
        brush = QBrush(Qt.SolidPattern)
        brush.setColor(self.color)
        painter.setPen(QPen(self.color))
        painter.setBrush(brush)

        # Draw marker shape
        shape_name = MARKERS[self.marker]['shape']
        if shape_name == 'circle':
            painter.drawEllipse(-4, -4, 8, 8)
        else:
            painter.drawPolygon(self.shapes[shape_name])

        # Draw marker label
        font = QFont()
        font.setFamily(FONT_FAMILY)
        font.setPixelSize(FONT_SIZE)
        font.setBold(FONT_BOLD)
        painter.setFont(font)
        painter.drawText(10, -2, self.label)
        
        # Draw marker depth
        font.setPixelSize(FONT_SIZE * 0.85)
        font.setBold(FONT_BOLD)
        painter.setFont(font)
        painter.drawText(10, 14, str(self.depth) + 'm')

    def boundingRect(self):
        return QRectF(0, 0, 10, 10)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setSelected(True)
            self.hide()
            # TODO why isn't this working?
            print(f'Selected: {self.label}')
        return super().mousePressEvent(event)


class MapScene(QtWidgets.QGraphicsScene):

    def __init__(self, filename):
        super().__init__()

        # Get the marker list
        marker_data = MarkerData(filename)

        # Calculate the minimum and maximum values for the grid
        ext = marker_data.get_extents()
        x_min = math.floor(ext[0][0]/MAJOR_GRID) * MAJOR_GRID
        x_max = math.ceil(ext[0][1]/MAJOR_GRID) * MAJOR_GRID
        y_min = math.floor(ext[1][0]/MAJOR_GRID) * MAJOR_GRID
        y_max = math.ceil(ext[1][1]/MAJOR_GRID) * MAJOR_GRID

        # Draw minor grid
        for x in range(x_min, x_max+1, MINOR_GRID):
            self.addLine(x, y_min, x, y_max, MINOR_GRID_COLOR)
        for y in range(y_min, y_max+1, MINOR_GRID):
            self.addLine(x_min, y, x_max, y, MINOR_GRID_COLOR)

        # Draw major grid
        for x in range(x_min, x_max+1, MAJOR_GRID):
            self.addLine(x, y_min, x, y_max, MAJOR_GRID_COLOR)
        for y in range(y_min, y_max+1, MAJOR_GRID):
            self.addLine(x_min, y, x_max, y, MAJOR_GRID_COLOR)

        # Draw markers
        for x, y, m, b, d, n in marker_data.get_markers():
            marker = MapMarker(m, b, d, True if n == 'x' else False)
            marker.setPos(x, y)
            self.addItem(marker)


class MapView(QtWidgets.QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.scale(INIT_SCALE, INIT_SCALE)
        self._zoom = 0
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(BACKGROUND_COLOR)

    def wheelEvent(self, event):
        factor = 0
        if event.angleDelta().y() > 0:
            factor = 1.02
            self._zoom += 1
            self.scale(factor, factor)
        elif event.angleDelta().y() < 0:
            factor = 0.98
            self._zoom -= 1
            self.scale(factor, factor)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    widget = MainWindow()
    widget.resize(WIN_WIDTH, WIN_HEIGHT)
    widget.show()

    sys.exit(app.exec())
