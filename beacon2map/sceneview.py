import logging
import math
from dataclasses import dataclass

from PySide6.QtCore import QEvent, QPointF, QRect, QRectF, Signal
from PySide6.QtGui import QColor, Qt
from PySide6.QtWidgets import QCheckBox, QGraphicsScene, QGraphicsView

from beacon2map.locations import Extents, LocationMap
from beacon2map.gridpoint import GridPoint
from beacon2map.config import config as cfg


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
        self.map = None
        self.gridpoints = []
        self._grid = None
        self._grid_visible = True
        self.color_scheme = None
        self.color_min = None
        self.color_max = None

    def initialize(self, map: LocationMap) -> None:
        logger.debug('MapScene : Scene init start')
        logger.debug('MapScene : Map is %s.', map)

        self.map = map
        self.set_color_limits()

        # Draw the grid based on the minimum and maximum gridpoint coordinates
        self.build_grid(self.map.extents)

        # If we are reloading the file,
        # remove all current gridpoints from the Scene
        if self.gridpoints:
            self.clear_gridpoints()

        # Draw GridPoints
        try:
            self.create_gridpoints(self.map)
        except ValueError as error:
            msg = f'\nFailed to draw gridpoints {error}'
            raise RuntimeError(msg) from error
        else:
            self.finished_drawing_gridpoints.emit()
            msg = f'MapScene : Scene init end. {len(self.gridpoints)} gridpoints added to scene.'
            logger.debug(msg)
            logger.debug(f'Total items in scene : {len(self.items())}.')


    def delete_gridpoint(self, gp: GridPoint) -> None:
        '''Remove GridPoint from the scene as well as from the list.'''
        try:
            self.removeItem(gp)
            self.gridpoints.remove(gp)
        except ValueError as e:
            msg = f'MapScene : Error deleting gridpoint {gp} : {e}.'
            raise ValueError(msg) from e

    def clear_gridpoints(self) -> None:
        '''Clear all the GridPoints in the scene.'''
        # We iterate backwards over the gridpoints list
        for i in range(len(self.gridpoints)-1, -1, -1):
            self.delete_gridpoint(self.gridpoints[i])
        logger.debug(f'Clear gridpoints done. GridPoints: {len(self.gridpoints)} Items: {len(self.items())}.')

    def create_gridpoints(self, map) -> None:
        # Draw the markers and add them to a list so we can keep track of them
        # (QGraphicsScene has other items besides markers, such as grid lines)
        for location in map.locations:
            try:
                self.add_gridpoint(location)
            except (ValueError, KeyError) as error:
                msg = f'\ndraw_gridpoint() failed with: {error}'
                raise ValueError(msg) from error

    def add_gridpoint(self, location) -> GridPoint:
        gp = GridPoint(source=location)
        self.update_gridpoint_from_source(gp)
        self.gridpoints.append(gp)
        self.addItem(gp)
        return gp

    def update_gridpoint_from_source(self, gp) -> None:
        '''Set the GridPoint values from the Location object.'''

        # Changing the title will change the QGraphicsItem boundingRect
        # so we need to call this first
        gp.prepareGeometryChange()

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

    def set_color_scheme(self, radio_button: bool):
        if radio_button:
            self.color_scheme = 'category'
        else:
            self.color_scheme = 'depth'
        self.refresh_gridpoints()

    def color_from_scheme(self, gp: GridPoint) -> QColor:
        # GridPoint color based on Done status and depth
        if self.color_scheme == 'category':
            if gp.source.done:
                color = cfg.marker_done_color
            else:
                color = QColor(cfg.categories[gp.source.category]['color'])
        else:
            hue = self.scale_value(
                gp.source.depth, self.color_min, self.color_max, 0, 60, inverted=True)
            lightness = self.scale_value(
                gp.source.depth, self.color_min, self.color_max, 60, 200, inverted=True)
            color = QColor.fromHsl(hue, 255, lightness)
        return color

    @staticmethod
    def scale_value(value, value_min, value_max, dest_min, dest_max, inverted=False):
        normalized = (value - value_min) / value_max
        if inverted:
            normalized = 1 - normalized
        scaled = normalized * (dest_max - dest_min) + dest_min
        return scaled

    def set_color_limits(self):
        self.color_min, self.color_max = self.map.extents.min_z, self.map.extents.max_z

    def refresh_gridpoints(self):
        self.set_color_limits()
        for gp in self.gridpoints:
            self.update_gridpoint_from_source(gp)
        logger.debug(f'Refreshed {len(self.gridpoints)} GridPoints.')
        

    def build_grid(self, extents: Extents) -> None:
        '''Build the grid based on the Locations' x & y extents.'''
        # If the grid already exists this means we are reloading the CSV file.
        # Since we need to draw the grid before the markers, we remove the grid
        # before drawing it back again
        if self._grid:
            self.removeItem(self._grid)

        # Small root node for grid lines,
        # so we can hide or show them as a group
        self._grid = self.addEllipse(
            -2, -2, 4, 4, QColor(cfg.major_grid_color))

        # Calculate the grid extents so as to encompass all gridpoints
        self.grid_extents = self.calculate_grid_extents(extents)

        # Draw the grid
        self.draw_grid(
            self.grid_extents, cfg.minor_grid, QColor(cfg.minor_grid_color))
        self.draw_grid(
            self.grid_extents, cfg.major_grid, QColor(cfg.major_grid_color))

        msg = f'Finished drawing grid ({len(self._grid.childItems())} lines).'
        logger.debug(msg)

        # Set the scene's bounding rect to the sum of its items,
        # in order to handle zooming.
        # Because this is slow we are only doing this once
        # using the grid lines (which enclose all other items),
        # before the gridpoints are added to the scene.
        self.setSceneRect(self.itemsBoundingRect())

    @staticmethod
    def calculate_grid_extents(extents: Extents) -> Extents:
        '''Calculate grid extents to encompass locations extents.'''
        grid = cfg.major_grid
        grid_extents = Extents(
            min_x=math.floor(extents.min_x/grid) * grid,
            max_x=math.ceil(extents.max_x/grid) * grid,
            min_y=math.floor(extents.min_y/grid) * grid,
            max_y=math.ceil(extents.max_y/grid) * grid
        )
        logger.debug(f'Grid : {grid_extents}')
        return  grid_extents

    def draw_grid(self, ex: Extents, step: int, color: QColor) -> None:
        for x in range(ex.min_x, ex.max_x+1, step):
            self.addLine(x, ex.min_y, x, ex.max_y, color).setParentItem(
                self._grid)
        for y in range(ex.min_y, ex.max_y+1, step):
            self.addLine(ex.min_x, y, ex.max_x, y, color).setParentItem(
                self._grid)

    def toggle_grid(self) -> None:
        '''Toggle grid visibily (SLOT from Main Window QAction).'''
        self._grid_visible = not self._grid_visible
        self._grid.setVisible(self._grid_visible)
        logger.debug(f'Set grid visibility to {self._grid.isVisible()}.')

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
