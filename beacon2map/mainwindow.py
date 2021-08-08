import os
import math
import logging

from PySide6.QtCore import (
    QPointF,
    QRect,
    QRectF,
    QSize,
    Qt,
    Signal
    )
from PySide6.QtWidgets import (
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QMainWindow,
    QWidget
    )
from PySide6.QtGui import (
    QAction,
    QColor,
    QPixmap
    )

from beacon2map.gridpoint import GridPoint

if os.path.isfile('configmine.py'):
    import configmine as config
else:
    import config

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    '''Main Window for the application.
    Used to set up menus, toolbar and status bar behavior.'''

    def __init__(self, app):
        super().__init__()

        self.setWindowTitle('Subnautica Map')
        self.statusBar().setEnabled(True)

        # We set the central widget but don't initialize it yet.
        # This allows the status bar to update properly,
        # after the window has been constructed.
        self.setCentralWidget(MainWidget())

        # Define Actions
        self._create_actions()

        # Define Menus
        menubar = self.menuBar()
        menu_file = menubar.addMenu('&File')
        menu_file.addAction(self.act_reload)
        menu_file.addAction(self.act_reset_zoom)

        menu_view = menubar.addMenu('&View')
        menu_view.addAction(self.act_toggle_grid)

        # Define Toolbar
        toolbar = self.addToolBar('Main')
        toolbar.setIconSize(QSize(25, 25))
        toolbar.setMovable(False)
        toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        toolbar.addAction(self.act_reload)
        toolbar.addAction(self.act_reset_zoom)

        # Initialize the central widget with the app location data
        self.centralWidget().initialize(app.locationmap)

    def _create_actions(self):
        '''Define and connect QAction objects
        for the menus and keyboard shortcuts.'''

        self.act_reload = QAction('&Reload CSV File', self)
        self.act_reload.setIcon(QPixmap(config.icon['reload']))
        self.act_reload.setShortcut(Qt.CTRL + Qt.Key_R)
        self.act_reload.setStatusTip('Reload CSV File')
        self.act_reload.setMenuRole(QAction.NoRole)
        self.act_reload.triggered.connect(self.centralWidget().reload)

        self.act_reset_zoom = QAction('&Reset Zoom', self)
        self.act_reset_zoom.setIcon(QPixmap(config.icon['reset_zoom']))
        self.act_reset_zoom.setShortcut(Qt.Key_Space)
        self.act_reset_zoom.setStatusTip('Reset Zoom')
        self.act_reset_zoom.setMenuRole(QAction.NoRole)
        self.act_reset_zoom.triggered.connect(self.centralWidget().reset_zoom)

        self.act_toggle_grid = QAction('Toggle &Grid', self)
        self.act_toggle_grid.setIcon(QPixmap(config.icon['grid']))
        self.act_toggle_grid.setShortcut(Qt.CTRL + Qt.Key_G)
        self.act_toggle_grid.setStatusTip('Toggle Grid')
        self.act_toggle_grid.setMenuRole(QAction.NoRole)
        self.act_toggle_grid.triggered.connect(self.centralWidget().toggle_grid)

    def selection_changed(self, item):
        '''Slot called whenever scene.selectionChanged Signal is emitted.'''

        # If an item has been selected, display its info in the Status Bar,
        # otherwise clear the Status Bar.
        if item:
            marker = item[0].source
            status = f'{marker.name} ({marker.category} @ {marker.depth}m) '
            status += f'({int(marker.x)},{int(marker.y)}: '
            status += f'{marker.bearing}) '
            if marker.description:
                status += f'[{marker.description}]'
            self.statusBar().showMessage(status)
        else:
            self.statusBar().clearMessage()

    def scene_finished_loading(self, scene):
        '''Slot called whenever scene.gridpoints_loaded Signal is emitted.'''

        # Display the relevant message in the Status Bar
        status = f'Loaded {len(scene.gridpoints)} locations.'
        self.statusBar().showMessage(status)


class MainWidget(QWidget):
    '''Main map widget. Initialized with empty attributes
    so it may be built after the window is constructed.'''

    def __init__(self):
        super().__init__()
        self.map = None
        self.scene = None
        self.view = None

    def initialize(self, map):
        '''Build the scene, view and layout for the widget
        based on the LocationMap object.'''
        self.map = map

        # Instantiate QGraphicsScene
        # Connect standard and custom Signals
        self.scene = MapScene()

        # Connect scene events to Main Window
        self.scene.selectionChanged.connect(
            lambda: self.parentWidget().selection_changed(self.scene.selectedItems()))
        self.scene.gridpoints_loaded.connect(
            lambda: self.parentWidget().scene_finished_loading(self.scene))

        # Instantiate QGraphicsView
        self.view = MapView()

        # Once we have both scene and view objects,
        # we initialize them with the proper values
        self.scene.initialize(self.map)
        self.view.initialize(self.scene)

        # ---- Main layout ----
        layout_outer = QHBoxLayout()

        # -- Map View layout --
        layout_view = QHBoxLayout()
        layout_view.addWidget(self.view)

        # Add layouts
        layout_outer.addLayout(layout_view)
        self.setLayout(layout_outer)

    def reload(self):
        self.scene.initialize(self.map)

    def reset_zoom(self):
        '''Reset the zoom level to the default.'''
        self.view.reset()

    def toggle_grid(self):
        self.scene.set_visible_grid()
        # TODO Handle the toggle and on/off properly

    # def paintEvent(self, event):
    #     qp = QPainter()
    #     qp.begin(self)
    #     pen = QPen()
    #     pen.setColor('black')
    #     qp.setPen(pen)
    #     qp.drawText(20, 15, 'HELLO')
    #     qp.end()


class MapScene(QGraphicsScene):
    # Custom Signal fired when markers have been loaded
    # (this needs to be defined at the class, not instance, level)
    gridpoints_loaded = Signal()

    def __init__(self):
        super().__init__()

        # Initialize marker data
        self.map = None
        self.gridpoints = []
        self.extents = None
        self.grid = None
        self._grid_visible = True

    def initialize(self, locationmap):
        self.map = locationmap

        # Define the markers x & y extents, used for drawing the grid
        self.extents = self.map.get_extents()

        # Draw the grid based on the minimum and maximum marker coordinates
        self.build_grid(self.extents)

        # Remove all current markers from QGraphicsScene
        # if we are reloading the file
        if self.map.elements > 0:
            for gp in self.gridpoints:
                self.removeItem(gp)
            self.gridpoints.clear()

        # Draw markers and emit done Signal
        self.draw_markers()
        self.gridpoints_loaded.emit()
        logger.info(f'Scene init done, {len(self.gridpoints)} gridpoints added')
        

    # Draw the markers and add them to a list so we can keep track of them
    # (QGraphicsScene has other items besides markers, such as grid lines)
    def draw_markers(self):
        for loc in self.map.locations:
            gp = GridPoint(loc.name, source_obj=loc)
            gp.subtitle = str(loc.depth) + 'm'

            # Set marker color
            if loc.done:
                gp.color = config.marker_done_color
            elif loc.depth >= 600:
                gp.color = config.marker_deep_color
            else:
                gp.color = QColor(config.markers[loc.category]['color'])
            
            gp.icon = config.markers[loc.category]['icon']
            gp.setPos(loc.x, loc.y)
            
            self.gridpoints.append(gp)
            self.addItem(gp)

    # Draw the grid based on the markers x & y extents
    def build_grid(self, extents):
        # If the grid already exists this means we are reloading the CSV file.
        # Since we need to draw the grid before the markers, we remove the grid
        # before drawing it back again
        if self.grid:
            self.removeItem(self.grid)

        x_min = math.floor(
            extents[0][0]/config.major_grid) * config.major_grid
        y_min = math.floor(
            extents[0][1]/config.major_grid) * config.major_grid
        x_max = math.ceil(
            extents[1][0]/config.major_grid) * config.major_grid
        y_max = math.ceil(
            extents[1][1]/config.major_grid) * config.major_grid

        # Root node for grid lines, so we can hide or show them as a group
        self.grid = self.addEllipse(-10, -10, 20, 20, config.major_grid_color)

        # Draw the grid
        bounds = (x_min, x_max, y_min, y_max)
        self.draw_grid(bounds, config.minor_grid, config.minor_grid_color)
        self.draw_grid(bounds, config.major_grid, config.major_grid_color)

        self.grid_x_min = x_min
        self.grid_x_max = x_max
        self.grid_y_min = y_min
        self.grid_y_max = y_max

    def draw_grid(self, bounds, step, color):
        x_min, x_max, y_min, y_max = bounds
        for x in range(x_min, x_max+1, step):
            self.addLine(x, y_min, x, y_max, color).setParentItem(self.grid)
        for y in range(y_min, y_max+1, step):
            self.addLine(x_min, y, x_max, y, color).setParentItem(self.grid)

    # Toggle the grid (Signal connected from MainWindow checkbox)
    def set_visible_grid(self):
        # self.grid.setVisible(state == Qt.Checked)
        self._grid_visible = not self._grid_visible
        self.grid.setVisible(self._grid_visible)
        self.update()


class MapView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(config.bg_color)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
    
    def initialize(self, scene: MapScene):
        self.setScene(scene)
        # TODO redo extents zooming properly
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
