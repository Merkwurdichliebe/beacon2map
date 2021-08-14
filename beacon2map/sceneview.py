import logging
import math
from collections import namedtuple

from PySide6.QtCore import QPointF, QRect, QRectF, Signal
from PySide6.QtGui import QColor, Qt
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

from beacon2map.locations import LocationMap
from beacon2map.gridpoint import GridPoint
from beacon2map.config import config as cfg

logger = logging.getLogger(__name__)

# Data structure to represent the status of SpinBoxes & ToolbarFilterWidget
SceneFilter = namedtuple(
    'SceneFilter', ['min', 'max', 'categories', 'include_done'])


class MapScene(QGraphicsScene):
    # Custom Signal fired when markers have been loaded
    # (this needs to be defined at the class, not instance, level)
    gridpoints_loaded = Signal()

    def __init__(self):
        super().__init__()

        # Initialize gridpoint data
        self.map = None
        self.gridpoints = []
        self.extents = None
        self.grid = None
        self._grid_visible = True

    def initialize(self, locationmap: LocationMap):
        logger.debug('MapScene : Scene init start')
        logger.debug('MapScene : Map is %s.', locationmap)

        # Draw the grid based on the minimum and maximum gridpoint coordinates
        self.build_grid(locationmap.extents)

        # If we are reloading the file,
        # remove all current gridpoints from the Scene
        if self.gridpoints:
            self.clear_gridpoints()

        # Draw markers and emit done Signal
        try:
            self.create_gridpoints(locationmap)
        except ValueError as error:
            msg = f'\nFailed to draw gridpoints {error}'
            raise RuntimeError(msg) from error
        else:
            self.gridpoints_loaded.emit()
            msg = 'MapScene : Scene init end. %s gridpoints added to scene.'
            logger.debug(msg, len(self.gridpoints))

    def delete_gridpoint(self, gp: GridPoint) -> None:
        try:
            self.removeItem(gp)
            self.gridpoints.remove(gp)
            logger.debug(f'Gridpoint deleted : {gp}.')
        except ValueError as e:
            msg = f'MapScene : Error deleting gridpoint {gp} : {e}.'
            raise ValueError(msg) from e

    def clear_gridpoints(self):
        for gp in self.gridpoints:
            self.removeItem(gp)
        self.gridpoints.clear()

    def create_gridpoints(self, locationmap):
        # Draw the markers and add them to a list so we can keep track of them
        # (QGraphicsScene has other items besides markers, such as grid lines)
        for location in locationmap.locations:
            try:
                gridpoint = GridPoint(source=location)
                self.update_gridpoint_from_source(gridpoint)
                self.gridpoints.append(gridpoint)
                self.addItem(gridpoint)
            except (ValueError, KeyError) as error:
                msg = f'\ndraw_gridpoint() failed with: {error}'
                raise ValueError(msg) from error

    @staticmethod
    def update_gridpoint_from_source(gp):
        # We pass the Location object instance to the GridPoint constructor
        # so that we can refer to Location attributes from the GridPoint itself.
        location = gp.source

        # GridPoint title and subtitle
        gp.title = location.name
        gp.subtitle = str(location.depth) + 'm'
        if location.description is not None:
            gp.subtitle += ' ' + cfg.symbol['has_description']

        # GridPoint color based on Done status and depth
        if location.done:
            gp.color = cfg.marker_done_color
        else:
            gp.color = QColor(cfg.categories[location.category]['color'])
        gp.hover_bg_color = QColor(cfg.hover_bg_color)
        gp.hover_fg_color = QColor(cfg.hover_fg_color)

        # GridPoint icon and position
        gp.icon = cfg.categories[location.category]['icon']
        gp.setPos(location.x, location.y)

        gp.update()

    def inspector_value_changed(self, gp):
        '''
        Update the modified gripdoint and then the entire scene
        (otherwise, if a modified title is shorter it isn't completely redrawn)
        '''
        self.update_gridpoint_from_source(gp)
        self.update()
        # FIXME avoid this by making sure the gridpoint boundingRect is refereshed later ?

    def build_grid(self, extents):
        '''Build the grid based on the Locations' x & y extents.'''
        # If the grid already exists this means we are reloading the CSV file.
        # Since we need to draw the grid before the markers, we remove the grid
        # before drawing it back again
        if self.grid:
            self.removeItem(self.grid)

        # Calculate the grid bounds so as to encompass all gridpoints
        bounds = self.grid_bounding_rect(extents)

        # Root node for grid lines, so we can hide or show them as a group
        self.grid = self.addEllipse(-10, -10, 20, 20, QColor(cfg.major_grid_color))

        # Draw the grid
        self.draw_grid(bounds, cfg.minor_grid, QColor(cfg.minor_grid_color))
        self.draw_grid(bounds, cfg.major_grid, QColor(cfg.major_grid_color))

        # Set the scene's bounding rect to the sum of its items.
        # Because this is slow we are only doing this once,
        # using the grid lines which enclose all other items,
        # before the gridpoints are added to the scene.
        self.setSceneRect(self.itemsBoundingRect())

    @staticmethod
    def grid_bounding_rect(extents):
        ext_min, ext_max = (extents.min_x, extents.min_y), (extents.max_x, extents.max_y)
        grid = cfg.major_grid
        x_min, y_min = (math.floor(axis/grid) * grid for axis in ext_min)
        x_max, y_max = (math.ceil(axis/grid) * grid for axis in ext_max)
        return (x_min, x_max, y_min, y_max)

    def draw_grid(self, bounds, step, color):
        x_min, x_max, y_min, y_max = bounds
        for x in range(x_min, x_max+1, step):
            self.addLine(x, y_min, x, y_max, color).setParentItem(self.grid)
        for y in range(y_min, y_max+1, step):
            self.addLine(x_min, y, x_max, y, color).setParentItem(self.grid)

    # Toggle the grid (Signal connected from MainWindow checkbox)
    def set_visible_grid(self):
        self._grid_visible = not self._grid_visible
        self.grid.setVisible(self._grid_visible)
        self.update()

    def filter(self, filt):
        '''Show or hide gridpoints based on filter conditions'''
        for point in self.gridpoints:
            if self.should_point_be_visible(point, filt):
                point.setVisible(True)
            else:
                if point.isVisible():
                    point.setVisible(False)

    @staticmethod
    def should_point_be_visible(gridpoint, filt: SceneFilter):
        '''Determine whether a point should be visible
        based on its properties and the required filter'''

        # Check if depth is within min-max spinbox limits
        in_depth_range = filt.min <= gridpoint.source.depth <= filt.max

        # Check if point is marked as 'done' and checkbox is set to include
        done_status = not (gridpoint.source.done and not filt.include_done)
        if (in_depth_range and
                (gridpoint.source.category in filt.categories) and
                done_status):
            return True
        return False


class MapView(QGraphicsView):
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
    def reset(self):
        self.resetTransform()
        self.scale(cfg.init_scale, cfg.init_scale)
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
