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
from PySide6.QtGui import (
    QColor, QFont, QFontMetrics, QIcon, QPen, QBrush, QPixmap, QPolygon)
from PySide6.QtCore import QPointF, QRect, QRectF, Qt, QPoint, Signal

from markerdata import MarkerData
from ui import UIPanel
import config


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        # Set main window properties
        self.setWindowTitle('Subnautica Map')

        # Instantiate QGraphicsScene
        # Connect standard and custom Signals
        self.scene = MapScene(config.filename)

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
        self.panel.cb_grid.stateChanged.connect(self.scene.set_visible_grid)
        self.scene.markers_loaded.connect(
            lambda: self.panel.update_stats(self.scene))
        self.scene.selectionChanged.connect(
            lambda: self.panel.selection_changed(self.scene.selectedItems()))
        layout_panel = QVBoxLayout()
        layout_panel.addWidget(self.panel)

        # Add layouts
        layout_outer.addLayout(layout_view)
        layout_outer.addLayout(layout_panel)

        self.setLayout(layout_outer)

        self.panel.update_stats(self.scene)

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
    def __init__(self, category, label, depth, done, desc):
        super().__init__()
        self.category = category
        self.label = label
        self.depth = depth
        self.depth_label = str(depth) + 'm'
        self.done = done
        self.desc = desc
        self.icon = config.markers[self.category]['icon']

        self.font_large = QFont()
        self.font_large.setFamily(config.font_family)
        self.font_large.setPixelSize(config.font_size)
        self.font_large.setBold(config.font_bold)

        self.font_small = QFont()
        self.font_small.setFamily(config.font_family)
        self.font_small.setPixelSize(config.font_size * 0.85)
        self.font_small.setBold(config.font_bold)

        self._hover = False

        if self.desc:
            self.depth_label += ' •'

        # Set Qt flags
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setFlag(QGraphicsItem.ItemIsFocusable)
        self.setAcceptHoverEvents(True)

        # Build QPolygon dictionary from icons coordinates
        self.icons = {}
        for k, v in config.icons.items():
            self.icons[k] = QPolygon(
                [QPoint(*point) for point in config.icons[k]])

        # Set marker color
        self.color = config.marker_done_color if self.done else QColor(
            config.markers[self.category]['color'])

    def paint(self, painter, option, widget):
        if self._hover:
            config.hover_bg_color.setAlpha(128)
            painter.setPen(Qt.NoPen)
            painter.setBrush(config.hover_bg_color)
            painter.drawRoundedRect(self.boundingRect(), 5, 5)

        if self.isSelected():
            painter.setPen(QPen(QColor('white'), 1))
            painter.setBrush(config.hover_bg_color)
            painter.drawRoundedRect(self.boundingRect(), 5, 5)

        color = config.hover_fg_color if (
            self._hover or self.isSelected()) else self.color
        brush = QBrush(Qt.SolidPattern)
        brush.setColor(color)
        painter.setPen(QPen(color))
        painter.setBrush(brush)

        # Draw marker icon
        if self.icon == 'circle':
            painter.drawEllipse(
                -config.circle, -config.circle,
                config.circle*2, config.circle*2)
        else:
            painter.drawPolygon(self.icons[self.icon])

        # Draw marker label
        painter.setFont(self.font_large)
        painter.drawText(
            config.label_offset_x, config.label_offset_y, self.label)

        # Draw marker depth
        painter.setFont(self.font_small)
        painter.drawText(config.label_offset_x,
                         config.label_offset_y + config.font_size,
                         self.depth_label)

    # Return the boundingRect of the marker
    # by uniting the label, depth and icon boundingRects.
    # https://stackoverflow.com/questions/68431451/
    def boundingRect(self):
        if self.icon == 'circle':
            rect_icon = QRect(-config.circle, -config.circle,
                              config.circle*2, config.circle*2)
        else:
            rect_icon = QRect(self.icons[self.icon].boundingRect())

        rect_label = QFontMetrics(self.font_large).boundingRect(
            self.label).translated(
                config.label_offset_x, config.label_offset_y)
        rect_depth = QFontMetrics(self.font_small).boundingRect(
            self.depth_label).translated(
                config.label_offset_x,
                config.label_offset_y + config.font_size)
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
        self.marker_data = None
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
        self.draw_grid(self.extents)

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
    def draw_grid(self, extents):
        # If the grid already exists this means we are reloading the CSV file.
        # Since we need to draw the grid before the markers, we remove the grid
        # before drawing it back again
        if self.grid:
            self.removeItem(self.grid)

        x_min = math.floor(
            extents[0][0]/config.major_grid) * config.major_grid
        x_max = math.ceil(
            extents[0][1]/config.major_grid) * config.major_grid
        y_min = math.floor(
            extents[1][0]/config.major_grid) * config.major_grid
        y_max = math.ceil(
            extents[1][1]/config.major_grid) * config.major_grid

        # Root node for grid lines, so we can hide or show them as a group
        root = self.addEllipse(-10, -10, 20, 20, config.major_grid_color)

        # Draw minor grid
        for x in range(x_min, x_max+1, config.minor_grid):
            self.addLine(x, y_min, x, y_max,
                         config.minor_grid_color).setParentItem(root)
        for y in range(y_min, y_max+1, config.minor_grid):
            self.addLine(x_min, y, x_max, y,
                         config.minor_grid_color).setParentItem(root)

        # Draw major grid
        for x in range(x_min, x_max+1, config.major_grid):
            self.addLine(x, y_min, x, y_max,
                         config.major_grid_color).setParentItem(root)
        for y in range(y_min, y_max+1, config.major_grid):
            self.addLine(x_min, y, x_max, y,
                         config.major_grid_color).setParentItem(root)

        self.grid = root
        self.grid_x_min = x_min
        self.grid_x_max = x_max
        self.grid_y_min = y_min
        self.grid_y_max = y_max

    # Toggle the grid (Signal connected from MainWindow checkbox)
    def set_visible_grid(self, state):
        self.grid.setVisible(state == Qt.Checked)
        self.update()


class MapView(QGraphicsView):
    def __init__(self, scene: MapScene):
        super().__init__(scene)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(config.bg_color)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

        self._zoom = 1
        self.scene_x_min = scene.grid_x_min
        self.scene_x_size = scene.grid_x_max - scene.grid_x_min
        self.scene_y_min = scene.grid_y_min
        self.scene_y_size = scene.grid_y_max - scene.grid_y_min
        self.scene_rect = QRect(self.scene_x_min, self.scene_y_min,
                                self.scene_x_size, self.scene_y_size)

        self.reset()

    # Reset the view's scale and position
    def reset(self):
        self.resetTransform()
        self.scale(config.init_scale, config.init_scale)
        self._zoom = 1
        self.centerOn(QPointF(0, 0))

    # Handle mousewheel zoom
    def wheelEvent(self, event):
        factor = 1 * (event.angleDelta().y() / 1000 + 1)

        view_rect = QRect(
            0, 0, self.viewport().width(), self.viewport().height())
        visible_scene_rect = QRectF(
            self.mapToScene(view_rect).boundingRect())
        
        view_width = visible_scene_rect.size().width()
        scene_width = self.scene_rect.size().width()
        view_height = visible_scene_rect.size().height()
        scene_height = self.scene_rect.size().height()
        
        if factor < 1 and (
            view_width < scene_width or view_height < scene_height):
            self.scale(factor, factor)
            self._zoom = self._zoom * factor
        elif factor > 1 and self._zoom < 3:
            self.scale(factor, factor)
            self._zoom = self._zoom * factor


if __name__ == '__main__':
    app = QApplication([])
    app.setWindowIcon(QIcon(QPixmap('img/app_icon.png')))
    widget = MainWindow()
    widget.resize(config.window_width, config.window_height)
    widget.show()

    sys.exit(app.exec())

# TODO Handle file not found
# TODO Fix zoom code when fast zooming out
# TODO File selection form
# TODO Marker type checkboxes
