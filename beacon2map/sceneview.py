#!/usr/bin/env python

import logging
import math
from dataclasses import dataclass

from PySide6.QtCore import QEvent, QPointF, QRect, QRectF, Signal
from PySide6.QtGui import QColor, Qt
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QRadioButton

from location import LocationMap
from gridpoint import GridPoint
from grid import Grid
from config import config as cfg
from utility import logit, scale_value


logger = logging.getLogger(__name__)


# Data structure to represent the status of SpinBoxes & ToolbarFilterWidget
@dataclass
class SceneFilter:
    min: int
    max: int
    categories: list
    include_done: bool


class MapScene(QGraphicsScene):
    '''Draw the grid and GridPoints, handles Filter requests.'''
    # Custom Signal fired when markers have been loaded
    # (this needs to be defined at the class, not instance, level)
    finished_drawing_gridpoints = Signal()

    def __init__(self):
        super().__init__()

        # Initialize gridpoint data
        self.map: LocationMap = None
        self.map = 2
        self.gridpoints = []
        self._grid = None
        self.color_min = None
        self.color_max = None
        self.color_scheme = 'category'

    def initialize(self, map: LocationMap) -> None:
        logger.debug(f'MapScene init start with {map}.')

        self.map = map
        self.set_color_limits()

        # Draw the grid based on the minimum and maximum gridpoint coordinates
        self.grid = Grid(self.map.extents)
        self.grid.major = cfg.major_grid
        self.grid.minor = cfg.minor_grid
        self.grid.major_color = cfg.major_grid_color
        self.grid.minor_color = cfg.minor_grid_color
        self.grid.setZValue(0)
        self.addItem(self.grid)

        # If we are reloading the file,
        # remove all current gridpoints from the Scene
        if self.gridpoints:
            self.clear_gridpoints()

        # Draw GridPoints
        try:
            self.create_gridpoints(self.map)
        except ValueError as e:
            raise RuntimeError(
                f'\nFailed to draw gridpoints {e}') from e
        else:
            self.finished_drawing_gridpoints.emit()

            logger.debug(
                'MapScene init end. '
                f'{len(self.gridpoints)} gridpoints added to scene. '
                f'Total items in scene : {len(self.items())}.'
            )

    def delete_gridpoint(self, gp: GridPoint) -> None:
        '''Remove GridPoint from the scene as well as from the list.'''
        try:
            self.removeItem(gp)
            self.gridpoints.remove(gp)
        except ValueError as e:
            raise ValueError(
                f'MapScene : Error deleting gridpoint {gp} : {e}.') from e

    def clear_gridpoints(self) -> None:
        '''Clear all the GridPoints in the scene.'''
        # We iterate backwards over the gridpoints list
        for i in range(len(self.gridpoints)-1, -1, -1):
            self.delete_gridpoint(self.gridpoints[i])
        logger.debug(
            'Clear gridpoints done. GridPoints: '
            f'{len(self.gridpoints)} Items: {len(self.items())}.')

    def create_gridpoints(self, map) -> None:
        # Draw the markers and add them to a list so we can keep track of them
        # (QGraphicsScene has other items besides markers, such as grid lines)
        for location in map.locations:
            try:
                self.add_gridpoint(location)
            except (ValueError, KeyError) as e:
                raise ValueError(
                    f'\ndraw_gridpoint() failed {e}') from e

    def add_gridpoint(self, location) -> GridPoint:
        gp = GridPoint(source=location)
        self.update_gridpoint_from_source(gp)
        self.gridpoints.append(gp)
        self.addItem(gp)
        gp.ensureVisible()
        return gp

    def new_gridpoint(self, location):
        gp = self.add_gridpoint(location)
        self.clearSelection()
        gp.setSelected(True)

    def modify_gridpoint(self, gp: GridPoint) -> None:
        self.update_gridpoint_from_source(gp)
        gp.ensureVisible()

    def update_gridpoint_from_source(self, gp) -> None:
        '''Set the GridPoint values from the Location object.'''

        location = gp.source

        # GridPoint title and subtitle
        gp.title = location.name
        gp.subtitle = str(location.depth) + 'm'
        if location.description is not None:
            gp.subtitle += ' ' + cfg.symbol['has_description']

        gp.color = self.color_from_scheme(gp)
        gp.hover_bg_color = QColor(cfg.hover_bg_color)
        gp.hover_fg_color = QColor(cfg.hover_fg_color)

        # GridPoint icon and position
        gp.icon = cfg.categories[location.category]['icon']
        gp.setPos(location.x, location.y)

    def set_color_scheme(self, scheme: str):
        self.color_scheme = scheme
        self.refresh_gridpoints()
        logger.debug(f'Color scheme set to: {self.color_scheme}.')

    def color_from_scheme(self, gp: GridPoint) -> QColor:
        if self.color_scheme == 'category':
            if gp.source.done:
                color = cfg.marker_done_color
            else:
                color = QColor(cfg.categories[gp.source.category]['color'])
        else:
            # FIXME color_min max is cumbersome here
            hue = scale_value(
                gp.source.depth, self.color_min, self.color_max, 120, 120, inverted=True)
            lightness = scale_value(
                gp.source.depth, self.color_min, self.color_max, 40, 240, inverted=True)
            color = QColor.fromHsl(hue, 255, lightness)
        return color

    def set_color_limits(self):
        self.color_min, self.color_max = self.map.extents.min_z, self.map.extents.max_z

    def refresh_gridpoints(self):
        self.set_color_limits()
        for gp in self.gridpoints:
            self.update_gridpoint_from_source(gp)
        logger.debug(f'Refreshed {len(self.gridpoints)} GridPoints.')

    def toggle_grid(self) -> None:
        '''Toggle grid visibily (SLOT from Main Window QAction).'''
        logger.debug(
            f'Setting grid visibility to {not self.grid.isVisible()}.')
        self.grid.setVisible(not self.grid.isVisible())

    def filter(self, filt: SceneFilter) -> None:
        '''Show or hide gridpoints based on filter conditions.'''
        for point in self.gridpoints:
            if self.should_be_visible(point, filt):
                point.setVisible(True)
            else:
                if point.isVisible():
                    point.setVisible(False)

    @staticmethod
    def should_be_visible(gridpoint, filt: SceneFilter) -> None:
        '''Determine whether a point should be visible
        based on its properties and the required filter.'''

        # Check if depth is within min-max spinbox limits
        in_range = filt.min <= gridpoint.source.depth <= filt.max

        # Check if category matches categories to include
        is_visible_category = gridpoint.source.category in filt.categories

        # Check if point is marked as 'done' and checkbox is set to include
        done_status = not (gridpoint.source.done and not filt.include_done)

        if (in_range and is_visible_category and done_status):
            return True
        return False


class MapView(QGraphicsView):
    '''Handle zooming and dragging.'''
    def __init__(self, scene: MapScene):
        super().__init__()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QColor(cfg.bg_color))
        self.setDragMode(QGraphicsView.ScrollHandDrag)

        self.setScene(scene)
        # TODO redo extents zooming properly
        self._zoom = 1
        self.reset()

    # Reset the view's scale and position
    def reset(self) -> None:
        self.resetTransform()
        self.scale(cfg.init_scale, cfg.init_scale)
        self._zoom = 1
        self.centerOn(QPointF(0, 0))

    # Handle mousewheel zoom
    def wheelEvent(self, event: QEvent) -> None:
        factor = 1 * (event.angleDelta().y() / 1000 + 1)

        view_rect = QRect(
            0, 0, self.viewport().width(), self.viewport().height())
        visible_scene_rect = QRectF(
            self.mapToScene(view_rect).boundingRect())

        view_width = visible_scene_rect.size().width()
        scene_width = self.sceneRect().size().width()
        view_height = visible_scene_rect.size().height()
        scene_height = self.sceneRect().size().height()

        if (0 < factor < 1) and (
                view_width < scene_width or view_height < scene_height):
            self.scale(factor, factor)
            self._zoom = self._zoom * factor
        elif factor > 1 and self._zoom < 3:
            self.scale(factor, factor)
            self._zoom = self._zoom * factor
