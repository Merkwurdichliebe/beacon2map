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
import pandas as pd
import math
from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QColor, QFont, QPen, QBrush, QPolygon, QPainter
from PySide6.QtCore import Qt, QRectF, QPoint


FILENAME = 'sub-sample.csv'


class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.scene = MapScene(FILENAME)
        self.view = MapView(self.scene)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.view)


class MapMarker(QtWidgets.QGraphicsItem):
    def __init__(self, marker, label, depth, done):
        super().__init__()
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations)
        self.marker = marker
        self.label = label
        self.depth = depth
        self.done = done
        self.icons = {
            'pod':         {'color': 'limegreen', 'shape': 'star'},
            'wreck':       {'color': 'bisque', 'shape': 'x'},
            'biome':       {'color': 'coral', 'shape': 'circle'},
            'interest':    {'color': 'gold', 'shape': 'triangle'},
            'alien':       {'color': 'orchid', 'shape': 'square'},
            'mur':         {'color': 'deepskyblue', 'shape': 'square'},
            'misc':        {'color': 'darkorange', 'shape': 'circle'}
            }
        self.done_color = QColor('slateblue')
        self.color = self.done_color if self.done else QColor(
            self.icons[self.marker]['color'])
        self.shapes = {
            'square': self.build_polygon(
                [(-4, -4), (4, -4), (4, 4), (-4, 4)]),
            'triangle': self.build_polygon(
                [(0, -4), (4, 4), (-4, 4)]),
            'star': self.build_polygon(
                [(-1, -1), (0, -5), (1, -1), (5, 4),
                 (0, 1), (-5, 4), (-1, -1)]),
            'x': self.build_polygon(
                [(0, -2), (3, -5), (5, -3), (2, 0), (5, 3),
                 (3, 5), (0, 2), (-3, 5), (-5, 3), (-2, 0), (-5, -3), (-3, -5)])
        }

    @staticmethod
    def build_polygon(coordinates):
        return QPolygon([QPoint(*point) for point in coordinates])

    def paint(self, painter, option, widget):
        p = QPainter()
        pen = QPen(self.color)
        brush = QBrush(Qt.SolidPattern)
        brush.setColor(self.color)
        painter.setPen(pen)
        painter.setBrush(brush)

        shape_name = self.icons[self.marker]['shape']
        if shape_name == 'circle':
            painter.drawEllipse(-4, -4, 8, 8)
        else:
            painter.drawPolygon(self.shapes[shape_name])
        font = QFont()
        font.setFamily("Helvetica")
        font.setPixelSize(16)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(10, -2, self.label)
        font.setPixelSize(14)
        font.setBold(False)
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

        # Draw the grid:

        # Major and minor grid intervals
        major_grid = 500
        minor_grid = 100

        # Get the marker list
        marker_list = MarkerList(filename)

        # Calculate the minimum and maximum values
        # for the grid
        x_min = math.floor(marker_list.extents_x[0]/major_grid) * major_grid
        x_max = math.ceil(marker_list.extents_x[1]/major_grid) * major_grid
        y_min = math.floor(marker_list.extents_y[0]/major_grid) * major_grid
        y_max = math.ceil(marker_list.extents_y[1]/major_grid) * major_grid

        # Draw minor grid
        for x in range(x_min, x_max+1, minor_grid):
            self.addLine(x, y_min, x, y_max, QColor('mediumblue'))
        for y in range(y_min, y_max+1, minor_grid):
            self.addLine(x_min, y, x_max, y, QColor('mediumblue'))

        # Draw major grid
        for x in range(x_min, x_max+1, major_grid):
            self.addLine(x, y_min, x, y_max, QColor('dodgerblue'))
        for y in range(y_min, y_max+1, major_grid):
            self.addLine(x_min, y, x_max, y, QColor('dodgerblue'))

        # Draw markers
        for x, y, m, b, d, n in marker_list.processed:
            marker = MapMarker(m, b, d, True if n == 'x' else False)
            marker.setPos(x, y)
            self.addItem(marker)


class MapView(QtWidgets.QGraphicsView):
    def __init__(self, parent):
        super(MapView, self).__init__(parent)
        self.scale(0.75, 0.75)
        self._zoom = 0
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QColor('darkblue'))

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


class MarkerList():
    def __init__(self, filename):
        # Constants
        REF_DEPTH = 100             # Depth of the reference beacon

        # Read CSV file
        # Distance,Bearing,Depth,Name,Done,Color,Marker,Description
        # 630,90,250,Foo,FALSE,red,o,Bar
        df = pd.read_csv(filename)

        # Calculate a horizontal distance to the reference point
        delta = df['Distance']**2 - (df['Depth']-REF_DEPTH)**2
        df['h'] = round(delta.apply(math.sqrt)).astype(int)

        # Reverse the bearing (CSV holds the heading to the reference)
        df['dir'] = (df['Bearing'] - 180) % 360

        # Calculate the x, y coordinates from the distance and heading
        df['x'] = (df['dir'].apply(
            math.radians).apply(math.sin) * df['h']).astype(int)
        # We inverse the y coordinates for Qt
        df['y'] = (df['dir'].apply(
            math.radians).apply(math.cos) * -1 * df['h']).astype(int)

        # Convert everything to lists
        x = df['x'].tolist()
        y = df['y'].tolist()
        marker = df['Marker'].tolist()
        label = df['Name'].tolist()
        depth = df['Depth'].tolist()
        done = df['Done'].tolist()

        self.processed = zip(x, y, marker, label, depth, done)

        self.extents_x = (df['x'].min(), df['x'].max())
        self.extents_y = (df['y'].min(), df['y'].max())


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    widget = MyWidget()
    widget.resize(2560, 1440)
    widget.show()

    sys.exit(app.exec())
