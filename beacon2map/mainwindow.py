import os
import math
import logging

from PySide6.QtCore import QPointF, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QGraphicsScene, QGraphicsView, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QSpinBox, QWidget
    )
from PySide6.QtGui import QAction, QColor, QGuiApplication, QPixmap

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

        try:
            self.locationmap = app.locationmap
        except RuntimeError as error:
            msg = f'\nMain Window initialization failed {error}'
            raise RuntimeError(msg) from error

        if self.locationmap is not None:
            self.initialize()

    def initialize(self):
        self.setWindowTitle('Subnautica Map')
        self.statusBar().setEnabled(True)
        self.resize(config.window_width, config.window_height)
        self.center_window()

        # We set the central widget but don't initialize it yet.
        # This allows the status bar to update properly,
        # after the window has been constructed.
        self.setCentralWidget(MainWidget())

        self._create_actions()
        self._create_menus()
        self._create_toolbar()

        self.populate_scene()

    def center_window(self):
        qt_rect = self.frameGeometry()
        center = QGuiApplication.primaryScreen().availableGeometry().center()
        qt_rect.moveCenter(center)
        self.move(qt_rect.topLeft())

    def populate_scene(self):
        '''Initialize the central widget with the app location data.
        Also functions as a slot connected to the QAction act_reload.
        '''
        try:
            self.centralWidget().populate_scene(self.locationmap)
        except RuntimeError as error:
            msg = f'\nMain Window Populate scene failed {error}'
            raise RuntimeError(msg) from error

    def _create_actions(self):
        '''Define and connect QAction objects
        for the menus and keyboard shortcuts.'''

        self.act_reload = QAction('&Reload CSV File', self)
        self.act_reload.setIcon(QPixmap(config.icon['reload']))
        self.act_reload.setShortcut(Qt.CTRL + Qt.Key_R)
        self.act_reload.setStatusTip('Reload CSV File')
        self.act_reload.setMenuRole(QAction.NoRole)
        self.act_reload.triggered.connect(self.populate_scene)

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

    def _create_menus(self):
        menubar = self.menuBar()
        menu_file = menubar.addMenu('&File')
        menu_file.addAction(self.act_reload)

        menu_view = menubar.addMenu('&View')
        menu_view.addAction(self.act_reset_zoom)
        menu_view.addAction(self.act_toggle_grid)

    def _create_toolbar(self):

        # Command buttons

        toolbar = self.addToolBar('Main')
        toolbar.setIconSize(QSize(25, 25))
        toolbar.setMovable(False)
        toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        toolbar.addAction(self.act_reload)
        toolbar.addAction(self.act_reset_zoom)
        toolbar.addAction(self.act_toggle_grid)

        toolbar.addSeparator()

        # Filter Widget

        self.filter_widget = ToolbarFilterWidget()
        toolbar.addWidget(self.filter_widget)

        # Connect Filter Widget Signals

        self.filter_widget.spin_min.valueChanged.connect(self.spin_value_changed)
        self.filter_widget.spin_max.valueChanged.connect(self.spin_value_changed)
        self.filter_widget.checkbox_include_done.stateChanged.connect(self.set_filter)
        self.filter_widget.btn_reset_filters.clicked.connect(self.reset_filters)
        for checkbox in self.filter_widget.category_checkbox.values():
            checkbox.stateChanged.connect(
                lambda state, cb=checkbox: self.category_checkbox_clicked(cb))

    def selection_changed(self, item):
        '''Slot called whenever scene.selectionChanged Signal is emitted.'''

        # If an item has been selected, display its info in the Status Bar,
        # otherwise clear the Status Bar.
        if item:
            gp = item[0].source
            status = f'{gp.name} ({gp.category} @ {gp.depth}m) '
            status += f'({int(gp.x)},{int(gp.y)}: '
            status += f'{gp.bearing}) '
            if gp.description:
                status += f'[{gp.description}]'
            self.statusBar().showMessage(status)
            logger.info('Gridpoint selected: %s', gp)
        else:
            self.statusBar().clearMessage()
            logger.info('No selection')

    def scene_finished_loading(self, scene):
        '''Slot called whenever scene.gridpoints_loaded Signal is emitted.'''

        # Display the relevant message in the Status Bar
        status = f'Loaded {len(scene.gridpoints)} locations.'
        self.statusBar().showMessage(status)

        # Reset the depth spin boxes to min-max values
        self.reset_filters()

    def reset_filters(self):
        min_loc_depth, max_loc_depth = self.locationmap.depth_extents
        self.filter_widget.spin_min.setMinimum(min_loc_depth)
        self.filter_widget.spin_min.setMaximum(max_loc_depth)
        self.filter_widget.spin_max.setMinimum(min_loc_depth)
        self.filter_widget.spin_max.setMaximum(max_loc_depth)
        self.filter_widget.spin_min.setValue(min_loc_depth)
        self.filter_widget.spin_max.setValue(max_loc_depth)
        for checkbox in self.filter_widget.category_checkbox.values():
            checkbox.blockSignals(True)
            checkbox.setChecked(True)
            checkbox.blockSignals(False)
        self.filter_widget.checkbox_include_done.setChecked(True)
        self.set_filter()

    def spin_value_changed(self):
        # Don't let the min and max value invert positions
        self.filter_widget.spin_min.setMaximum(self.filter_widget.spin_max.value())
        self.filter_widget.spin_max.setMinimum(self.filter_widget.spin_min.value())
        self.set_filter()

    def category_checkbox_clicked(self, current_cb):
        # Use Command Key for exclusive checkbox behavior
        if self.is_command_key_held():
            for cb in self.filter_widget.category_checkbox.values():
                if cb is not current_cb:
                    cb.blockSignals(True)
                    cb.setChecked(not current_cb.isChecked())
                    cb.blockSignals(False)
        self.set_filter()

    def set_filter(self):
        categories = []
        for k, v in self.filter_widget.category_checkbox.items():
            if v.isChecked():
                categories.append(k)
        done = self.filter_widget.checkbox_include_done.isChecked()
        filt = (self.filter_widget.spin_min.value(), self.filter_widget.spin_max.value(), categories, done)
        self.centralWidget().filter(filt)

    @staticmethod
    def is_command_key_held():
        return QGuiApplication.keyboardModifiers() == Qt.ControlModifier


class MainWidget(QWidget):
    '''Main map widget. Sets up the Scene and View.'''

    def __init__(self):
        super().__init__()

        # Setup QGraphicsScene
        self.scene = MapScene()
        self.scene.selectionChanged.connect(
            lambda: self.parentWidget().selection_changed(self.scene.selectedItems()))
        self.scene.gridpoints_loaded.connect(
            lambda: self.parentWidget().scene_finished_loading(self.scene))

        # Setup QGraphicsView & layout
        self.view = MapView(self.scene)
        layout = QHBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

    def reset_zoom(self):
        self.view.reset()

    def populate_scene(self, locationmap):
        try:
            self.scene.initialize(locationmap)
        except RuntimeError as error:
            msg = f'\nMainWidget Populate scene failed {error}'
            raise RuntimeError(msg) from error

    def toggle_grid(self):
        self.scene.set_visible_grid()

    def filter(self, filt):
        self.scene.filter(filt)


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

    def initialize(self, locationmap):
        logger.info('MapScene: Scene init start')
        self.map = locationmap
        logger.info('MapScene: Map is %s', self.map)

        # Define the girdpoints x & y extents, used for drawing the grid
        self.extents = self.map.get_extents()

        # Draw the grid based on the minimum and maximum gridpoint coordinates
        self.build_grid()

        # If we are reloading the file,
        # remove all current gridpoints from the Scene
        if self.gridpoints:
            self.clear_gridpoints()

        # Draw markers and emit done Signal
        try:
            self.draw_gridpoints()
        except ValueError as error:
            msg = f'\nFailed to draw gridpoints {error}'
            raise RuntimeError(msg) from error
        else:
            self.gridpoints_loaded.emit()
            logger.info('MapScene: Scene init done, %s gridpoints added', len(self.gridpoints))

    def clear_gridpoints(self):
        for gp in self.gridpoints:
            self.removeItem(gp)
        self.gridpoints.clear()

    def draw_gridpoints(self):
        # Draw the markers and add them to a list so we can keep track of them
        # (QGraphicsScene has other items besides markers, such as grid lines)
        #
        # We pass the Location object instance to the GridPoint constructor
        # so that we can refer to Location attributes from the GridPoint itself.
        for loc in self.map.locations:
            try:
                # GridPoint title and subtitle
                gp = GridPoint(loc.name, source_obj=loc)
                gp.subtitle = str(loc.depth) + 'm'
                if loc.description is not None:
                    gp.subtitle += ' ' + config.symbol['has_description']

                # GridPoint color based on Done status and depth
                if loc.done:
                    gp.color = config.marker_done_color
                else:
                    gp.color = QColor(config.categories[loc.category]['color'])
                gp.hover_bg_color = config.hover_bg_color
                gp.hover_fg_color = config.hover_fg_color

                # GridPoint icon and position
                gp.icon = config.categories[loc.category]['icon']
                gp.setPos(loc.x, loc.y)

                self.gridpoints.append(gp)
                self.addItem(gp)
            except (ValueError, KeyError) as error:
                msg = f'\ndraw_gridpoint() failed with: {error}'
                raise ValueError(msg) from error

    def build_grid(self):
        '''Build the grid based on the Locations' x & y extents.'''
        # If the grid already exists this means we are reloading the CSV file.
        # Since we need to draw the grid before the markers, we remove the grid
        # before drawing it back again
        if self.grid:
            self.removeItem(self.grid)

        # Calculate the grid extents so as to encompass all gridpoints
        extents_min, extents_max = self.extents
        grid = config.major_grid
        x_min, y_min = (math.floor(axis/grid) * grid for axis in extents_min)
        x_max, y_max = (math.ceil(axis/grid) * grid for axis in extents_max)

        # Root node for grid lines, so we can hide or show them as a group
        self.grid = self.addEllipse(-10, -10, 20, 20, config.major_grid_color)

        # Draw the grid
        bounds = (x_min, x_max, y_min, y_max)
        self.draw_grid(bounds, config.minor_grid, config.minor_grid_color)
        self.draw_grid(bounds, config.major_grid, config.major_grid_color)

        # Set the scene's bounding rect to the sum of its items.
        # Because this is slow we are only doing this once,
        # using the grid lines which enclose all other items,
        # before the gridpoints are added to the scene.
        self.setSceneRect(self.itemsBoundingRect())

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
    def should_point_be_visible(gridpoint, filt):
        '''Determine whether a point should be visible
        based on its properties and the required filter'''
        min_depth, max_depth, categories, include_done = filt
        # Check if depth is within min-max spinbox limits
        in_depth_range = min_depth <= gridpoint.source.depth <= max_depth
        # Check if point is marked as 'done' and checkbox is set to include
        done_status = not (gridpoint.source.done and not include_done)
        if (in_depth_range and
                (gridpoint.source.category in categories) and
                done_status):
            return True
        return False


class ToolbarFilterWidget(QWidget):
    '''A subclass of QWidget which holds several UI controls
    grouped together into a filter panel which can be added
    to the QToolBar as group.'''
    # Originally created in order to solve a vertical alignment problem
    # with the Reset Filter button.
    # https://forum.qt.io/topic/129244/qpushbutton-vertical-alignment-in-qtoolbar/5
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()

        lbl_spin_min = QLabel('Min depth', self)
        lbl_spin_min.setStyleSheet('QLabel {padding: 0 10}')
        layout.addWidget(lbl_spin_min)

        self.spin_min = DepthSpinBox(self)
        layout.addWidget(self.spin_min)

        lbl_spin_max = QLabel('Max depth', self)
        lbl_spin_max.setStyleSheet('QLabel {padding: 0 10}')
        layout.addWidget(lbl_spin_max)

        self.spin_max = DepthSpinBox(self)
        layout.addWidget(self.spin_max)

        self.category_checkbox = {}
        for cat in config.categories:
            self.category_checkbox[cat] = QCheckBox(cat.capitalize())
            layout.addWidget(self.category_checkbox[cat])

        self.checkbox_include_done = QCheckBox('Include Done')
        layout.addWidget(self.checkbox_include_done)

        self.btn_reset_filters = QPushButton('Reset Filters')
        layout.addWidget(self.btn_reset_filters)

        self.setLayout(layout)


class MapView(QGraphicsView):
    def __init__(self, scene: MapScene):
        super().__init__()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(config.bg_color)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

        self.setScene(scene)
        # TODO redo extents zooming properly
        self._zoom = 1
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


class DepthSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSingleStep(5)
        self.setAlignment(Qt.AlignRight)
        self.setFixedWidth(60)
