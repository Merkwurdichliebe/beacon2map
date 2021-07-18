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
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QCheckBox,
    QGraphicsScene, QGraphicsView, QGraphicsItem
    )
from PySide6.QtGui import QColor, QFont, QPen, QBrush, QPolygon, QPainter
from PySide6.QtCore import QPointF, Qt, QRectF, QPoint

from markerdata import MarkerData

FILENAME = 'sub.csv'

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


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Subnautica Map')

        self.scene = MapScene(FILENAME)
        self.view = MapView(self.scene)

        # Main layout
        layout_outer = QHBoxLayout()

        # Map layout
        layout_view = QVBoxLayout()
        layout_view.addWidget(self.view)

        # Panel layout
        layout_panel = QVBoxLayout()
        cb_grid = QCheckBox('Grid')
        cb_grid.toggle()
        cb_grid.stateChanged.connect(self.scene.setVisibleGrid)
        layout_panel.addWidget(cb_grid)

        # Add layouts
        layout_outer.addLayout(layout_view)
        layout_outer.addLayout(layout_panel)

        self.setLayout(layout_outer)

    def keyPressEvent(self, e):
        if e.key() == 32:
            self.view.reset()
        else:
            return super().keyPressEvent(e)


class MapMarker(QGraphicsItem):
    def __init__(self, marker, label, depth, done):
        super().__init__()
        self.marker = marker
        self.label = label
        self.depth = depth
        self.done = done

        # Set Qt flags
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setFlag(QGraphicsItem.ItemIsFocusable)

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

        if self.isSelected():
            self.drawFocusRect(painter)

    def boundingRect(self):
        return QRectF(-10, -15, 200, 30)
        # return self.childrenBoundingRect()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setSelected(True)
            # self.hide()
            # self.scene().update()
            print(f'Selected: {self.label}')
        return super().mousePressEvent(event)

    def drawFocusRect(self, painter):
        self.focusbrush = QBrush()
        self.focuspen = QPen(QtCore.Qt.DotLine)
        self.focuspen.setColor(QtCore.Qt.black)
        self.focuspen.setWidthF(1.5)
        painter.setBrush(self.focusbrush)
        painter.setPen(self.focuspen)
        painter.drawRect(self.focusrect)

    def hoverEnterEvent(self, event):
        self.pen.setStyle(QtCore.Qt.DotLine)
        QGraphicsItem.hoverEnterEvent(self, event)


class MapScene(QGraphicsScene):

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

        root = self.addEllipse(-10, -10, 20, 20, MAJOR_GRID_COLOR)

        # Draw minor grid
        for x in range(x_min, x_max+1, MINOR_GRID):
            self.addLine(x, y_min, x, y_max, MINOR_GRID_COLOR).setParentItem(root)
        for y in range(y_min, y_max+1, MINOR_GRID):
            self.addLine(x_min, y, x_max, y, MINOR_GRID_COLOR).setParentItem(root)

        # Draw major grid
        for x in range(x_min, x_max+1, MAJOR_GRID):
            self.addLine(x, y_min, x, y_max, MAJOR_GRID_COLOR).setParentItem(root)
        for y in range(y_min, y_max+1, MAJOR_GRID):
            self.addLine(x_min, y, x_max, y, MAJOR_GRID_COLOR).setParentItem(root)

        self.grid = root

        # Draw markers
        for x, y, m, b, d, n in marker_data.get_markers():
            marker = MapMarker(m, b, d, True if n == 'x' else False)
            marker.setPos(x, y)
            self.addItem(marker)

    def setVisibleGrid(self, state):
        self.grid.setVisible(state == Qt.Checked)
        self.update()


class MapView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self._zoom = 0
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(BACKGROUND_COLOR)
        self.reset()

    def reset(self):
        self.resetTransform()
        self.scale(INIT_SCALE, INIT_SCALE)
        self._zoom = 0
        self.centerOn(QPointF(0, 0))

    def wheelEvent(self, event):
        factor = 1 * (event.angleDelta().y() / 1000 + 1)
        self.scale(factor, factor)


if __name__ == '__main__':
    app = QApplication([])
    widget = MainWindow()
    widget.resize(WIN_WIDTH, WIN_HEIGHT)
    widget.show()

    sys.exit(app.exec())
