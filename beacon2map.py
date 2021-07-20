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

from PySide6 import QtCore
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QGraphicsScene, QGraphicsView, QGraphicsItem
    )
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPen, QBrush, QPixmap, QPolygon
from PySide6.QtCore import QPointF, QRect, Qt, QPoint, Signal

from markerdata import MarkerData
from qt import UIPanel

FILENAME = 'sub-sample.csv'

MAJOR_GRID = 500
MINOR_GRID = 100

MAJOR_GRID_COLOR = QColor('dodgerblue')
MINOR_GRID_COLOR = QColor('mediumblue')
BACKGROUND_COLOR = QColor('darkblue')
MARKER_DONE_COLOR = QColor('slateblue')
HOVER_BG_COLOR = QColor('lime')
HOVER_FG_COLOR = QColor('white')

INIT_SCALE = 0.75
WIN_WIDTH = 2560
WIN_HEIGHT = 1440

FONT_FAMILY = 'Helvetica'
FONT_SIZE = 16
FONT_BOLD = True
LABEL_OFFSET_X = 10
LABEL_OFFSET_Y = -2

MARKERS = {
    'pod':         {'color': 'limegreen', 'icon': 'star'},
    'wreck':       {'color': 'coral', 'icon': 'x'},
    'biome':       {'color': 'limegreen', 'icon': 'circle'},
    'interest':    {'color': 'gold', 'icon': 'triangle'},
    'alien':       {'color': 'fuchsia', 'icon': 'square'},
    'mur':         {'color': 'deepskyblue', 'icon': 'square'},
    'misc':        {'color': 'darkorange', 'icon': 'circle'}
    }

ICONS = {
    'square': [(-4, -4), (4, -4), (4, 4), (-4, 4)],
    'triangle': [(0, -4), (4, 4), (-4, 4)],
    'star': [(-1, -1), (0, -5), (1, -1), (5, 4), (0, 1), (-5, 4), (-1, -1)],
    'x': [(0, -2), (3, -5), (5, -3), (2, 0), (5, 3),
          (3, 5), (0, 2), (-3, 5), (-5, 3), (-2, 0), (-5, -3), (-3, -5)]
    }

CIRCLE = 4  # Radius in pixels


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Set main window properties
        self.setWindowTitle('Subnautica Map')

        # Instantiate QGraphicsScene
        # Connect standard and custom Signals
        self.scene = MapScene(FILENAME)
        self.scene.selectionChanged.connect(self.update_marker_box)

        # Instantiate QGraphicsView
        self.view = MapView(self.scene)

        # ---- Main layout ----
        layout_outer = QHBoxLayout()

        # -- Map View layout --
        layout_view = QVBoxLayout()
        layout_view.addWidget(self.view)

        # -- Panel layout --
        self.panel = UIPanel()
        self.panel.btn_reload.clicked.connect(self.reload)
        self.panel.cb_grid.stateChanged.connect(self.scene.setVisibleGrid)
        self.scene.markers_loaded.connect(self.update_panel)
        layout_panel = QVBoxLayout()
        layout_panel.addWidget(self.panel)

        # Add layouts
        layout_outer.addLayout(layout_view)
        layout_outer.addLayout(layout_panel)

        self.setLayout(layout_outer)

        self.update_panel()
        self.update_marker_box()

    def update_panel(self):
        self.panel.update_stats(self.scene)

    def update_marker_box(self):
        self.panel.marker_box.update(self.scene)

    def reload(self):
        self.scene.initialize()
        self.panel.cb_grid.setChecked(True)

    # Reset the view when Spacebar is pressed
    def keyPressEvent(self, e):
        if e.key() == 32:
            self.view.reset()
        else:
            return super().keyPressEvent(e)


class MapMarker(QGraphicsItem):
    def __init__(self, marker, label, depth, done, desc):
        super().__init__()
        self.marker = marker
        self.label = label
        self.depth = depth
        self.depth_label = str(depth) + 'm'
        self.done = done
        self.desc = desc
        self.icon = MARKERS[self.marker]['icon']
        self.font_large = QFont(FONT_FAMILY, FONT_SIZE)
        self.font_large.setBold(FONT_BOLD)
        self.font_small = QFont(FONT_FAMILY, FONT_SIZE * 0.85)
        self.font_small.setBold(FONT_BOLD)
        self._hover = False

        if self.desc:
            self.depth_label += ' •'

        # Set Qt flags
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setFlag(QGraphicsItem.ItemIsFocusable)
        self.setAcceptHoverEvents(True)

        # Build QPolygon dictionary from iconS coordinates
        self.icons = {}
        for k, v in ICONS.items():
            self.icons[k] = QPolygon([QPoint(*point) for point in ICONS[k]])

        # Set marker color
        self.color = MARKER_DONE_COLOR if self.done else QColor(
            MARKERS[self.marker]['color'])

    def paint(self, painter, option, widget):
        if self._hover:
            HOVER_BG_COLOR.setAlpha(128)
            painter.setPen(Qt.NoPen)
            painter.setBrush(HOVER_BG_COLOR)
            painter.drawRoundedRect(self.boundingRect(), 5, 5)

        if self.isSelected():
            painter.setPen(QPen(QColor('white'), 1))
            painter.setBrush(HOVER_BG_COLOR)
            painter.drawRoundedRect(self.boundingRect(), 5, 5)

        color = HOVER_FG_COLOR if (
            self._hover or self.isSelected()) else self.color
        brush = QBrush(Qt.SolidPattern)
        brush.setColor(color)
        painter.setPen(QPen(color))
        painter.setBrush(brush)

        # Draw marker icon
        if self.icon == 'circle':
            painter.drawEllipse(
                -CIRCLE, -CIRCLE, CIRCLE*2, CIRCLE*2)
        else:
            painter.drawPolygon(self.icons[self.icon])

        # Draw marker label
        painter.setFont(self.font_large)
        painter.drawText(LABEL_OFFSET_X, LABEL_OFFSET_Y, self.label)

        # Draw marker depth
        painter.setFont(self.font_small)
        painter.drawText(LABEL_OFFSET_X,
                         LABEL_OFFSET_Y + FONT_SIZE,
                         self.depth_label)

    # Return the boundingRect of the marker
    # by uniting the label, depth and icon boundingRects.
    # https://stackoverflow.com/questions/68431451/
    def boundingRect(self):
        if self.icon == 'circle':
            rect_icon = QRect(-CIRCLE, -CIRCLE, CIRCLE*2, CIRCLE*2)
        else:
            rect_icon = QRect(self.icons[self.icon].boundingRect())

        rect_label = QFontMetrics(self.font_large).boundingRect(
            self.label).translated(
                LABEL_OFFSET_X, LABEL_OFFSET_Y)
        rect_depth = QFontMetrics(self.font_small).boundingRect(
            self.depth_label).translated(
                LABEL_OFFSET_X, LABEL_OFFSET_Y + FONT_SIZE)
        return (rect_label | rect_depth | rect_icon).adjusted(-10, -5, 10, 5)

    def hoverEnterEvent(self, e):
        self._hover = True
        self.update()
        return super().hoverLeaveEvent(e)

    def hoverLeaveEvent(self, e):
        self._hover = False
        self.update()
        return super().hoverLeaveEvent(e)


class MapScene(QGraphicsScene):
    # Custom Signal fired when markers have been loaded
    # (this needs to be defined at the class, not instance, level)
    markers_loaded = Signal()

    def __init__(self, filename):
        super().__init__()

        # Initialize marker data
        self.filename = filename
        self.markers = []
        self.extents = None
        self.grid = None
        self.initialize()

    def initialize(self):
        # Read the marker data
        self.marker_data = MarkerData(self.filename)

        # Define the markers x & y extents, used for drawing the grid
        self.extents = self.marker_data.get_extents()

        # Draw the grid based on the minimum and maximum marker coordinates
        self.drawGrid(self.extents)

        # Remove all current markers from QGraphicsScene
        # if we are reloading the file
        if len(self.markers) > 0:
            for marker in self.markers:
                self.removeItem(marker)
            self.markers.clear()

        # Draw markers and emit done Signal
        self.draw_markers()
        self.markers_loaded.emit()

    # Draw the markers and add them to a list so we can keep track of them
    # (QGraphicsScene has other items besides markers, such as grid lines)
    def draw_markers(self):
        for x, y, m, b, d, n, p in self.marker_data.get_markers():
            marker = MapMarker(m, b, d, True if n == 'x' else False, p)
            marker.setPos(x, y)
            self.markers.append(marker)
            self.addItem(marker)

    # Draw the grid based on the markers x & y extents
    def drawGrid(self, extents):
        # If the grid already exists this means we are reloading the CSV file.
        # Since we need to draw the grid before the markers, we remove the grid
        # before drawing it back again
        if self.grid:
            self.removeItem(self.grid)

        x_min = math.floor(extents[0][0]/MAJOR_GRID) * MAJOR_GRID
        x_max = math.ceil(extents[0][1]/MAJOR_GRID) * MAJOR_GRID
        y_min = math.floor(extents[1][0]/MAJOR_GRID) * MAJOR_GRID
        y_max = math.ceil(extents[1][1]/MAJOR_GRID) * MAJOR_GRID

        # Root node for grid lines, so we can hide or show them as a group
        root = self.addEllipse(-10, -10, 20, 20, MAJOR_GRID_COLOR)

        # Draw mino grid
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

    # Toggle the grid (Signal connected from MainWindow checkbox)
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

    # Reset the view's scale and position
    def reset(self):
        self.resetTransform()
        self.scale(INIT_SCALE, INIT_SCALE)
        self._zoom = 0
        self.centerOn(QPointF(0, 0))

    # Handle mousewheel zoom
    def wheelEvent(self, event):
        factor = 1 * (event.angleDelta().y() / 1000 + 1)
        self.scale(factor, factor)


if __name__ == '__main__':
    app = QApplication([])
    app.setWindowIcon(QIcon(QPixmap('img/app_icon.png')))
    widget = MainWindow()
    widget.resize(WIN_WIDTH, WIN_HEIGHT)
    widget.show()

    sys.exit(app.exec())

# TODO File not found
