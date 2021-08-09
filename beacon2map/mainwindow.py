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
    QCheckBox,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QWidget
    )
from PySide6.QtGui import (
    QAction,
    QColor,
    QGuiApplication,
    QPixmap,
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

        self.locationmap = app.locationmap

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
        self.centralWidget().populate_scene(self.locationmap)

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

        # Depth spin boxes

        lbl_spin_min = QLabel('Min depth')
        lbl_spin_min.setStyleSheet('QLabel {padding: 0 10}')
        toolbar.addWidget(lbl_spin_min)

        self.spin_min = DepthSpinBox()
        toolbar.addWidget(self.spin_min)

        lbl_spin_max = QLabel('Max depth')
        lbl_spin_max.setStyleSheet('QLabel {padding: 0 10}')
        toolbar.addWidget(lbl_spin_max)

        self.spin_max = DepthSpinBox()
        toolbar.addWidget(self.spin_max)

        self.spin_min.valueChanged.connect(self.spin_value_changed)
        self.spin_max.valueChanged.connect(self.spin_value_changed)

        toolbar.addSeparator()

        # Category filter checkboxes

        self.category_checkbox = {}
        for cat in config.categories:
            cbox = QCheckBox(cat.capitalize())
            toolbar.addWidget(cbox)
            self.category_checkbox[cat] = cbox
            self.category_checkbox[cat].stateChanged.connect(
                lambda state, cb=cbox: self.category_checkbox_clicked(cb))

        toolbar.addSeparator()

        # Reset Filters button

        self.btn_reset_filters = QPushButton('Reset Filters')
        toolbar.addWidget(self.btn_reset_filters)

        self.btn_reset_filters.clicked.connect(self.reset_filters)

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

        # Reset the depth spin boxes to min-max values
        self.reset_filters()

    def reset_filters(self):
        min_loc_depth, max_loc_depth = self.locationmap.depth_extents
        self.spin_min.setMinimum(min_loc_depth)
        self.spin_min.setMaximum(max_loc_depth)
        self.spin_min.setMinimum(min_loc_depth)
        self.spin_max.setMaximum(max_loc_depth)
        self.spin_min.setValue(min_loc_depth)
        self.spin_max.setValue(max_loc_depth)
        for checkbox in self.category_checkbox.values():
            checkbox.setChecked(True)
        self.filter()

    def spin_value_changed(self):
        # Don't let the min and max value invert positions
        self.spin_min.setMaximum(self.spin_max.value())
        self.spin_max.setMinimum(self.spin_min.value())
        self.filter()

    def category_checkbox_clicked(self, current_cb):
        # Use Command Key for exclusive checkbox behavior
        if self.is_command_key_held():
            for cb in self.category_checkbox.values():
                if cb is not current_cb:
                    cb.blockSignals(True)
                    cb.setChecked(not current_cb.isChecked())
                    cb.blockSignals(False)
        self.filter()

    def filter(self):
        categories = []
        for k, v in self.category_checkbox.items():
            if v.isChecked():
                categories.append(k)
        filt = (self.spin_min.value(), self.spin_max.value(), categories)
        self.centralWidget().scene.filter(filt)

    @staticmethod
    def is_command_key_held():
        return QGuiApplication.keyboardModifiers() == Qt.ControlModifier

class MainWidget(QWidget):
    '''Main map widget.'''

    def __init__(self):
        super().__init__()

        # Instantiate QGraphicsScene
        self.scene = MapScene()

        # Connect scene events to Main Window
        self.scene.selectionChanged.connect(
            lambda: self.parentWidget().selection_changed(self.scene.selectedItems()))
        self.scene.gridpoints_loaded.connect(
            lambda: self.parentWidget().scene_finished_loading(self.scene))

        # Instantiate QGraphicsView
        self.view = MapView(self.scene)

        # ---- Main layout ----
        layout_outer = QHBoxLayout()

        # -- Map View layout --
        layout_view = QHBoxLayout()
        layout_view.addWidget(self.view)

        # Add layouts
        layout_outer.addLayout(layout_view)
        self.setLayout(layout_outer)

    def populate_scene(self, locationmap):
        self.scene.initialize(locationmap)

    def reset_zoom(self):
        self.view.reset()
        self.parentWidget().act_toggle_grid.setIcon(QPixmap(config.icon['reload']))

    def toggle_grid(self):
        self.scene.set_visible_grid()

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
        logger.info('MapScene: Scene init start')

        self.map = locationmap
        logger.info('MapScene: Map is %s', self.map)

        # Define the markers x & y extents, used for drawing the grid
        self.extents = self.map.get_extents()

        # Draw the grid based on the minimum and maximum marker coordinates
        self.build_grid()

        # Remove all current markers from QGraphicsScene
        # if we are reloading the file
        if self.gridpoints:
            self.clear_gridpoints()

        # Draw markers and emit done Signal
        try:
            self.draw_gridpoints()
        except ValueError:
            print('lkjsdf')
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
            # GridPoint title and subtitle
            gp = GridPoint(loc.name, source_obj=loc)
            gp.subtitle = str(loc.depth) + 'm'

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
        '''Show or hide gridpoints based on filter conditions
        (min_depth, max_depth, categories)'''
        min_depth, max_depth, cats = filt
        for point in self.gridpoints:
            in_depth_range = min_depth < point.source.depth < max_depth
            if in_depth_range and point.source.category in cats:
                point.setVisible(True)
            else:
                point.setVisible(False)


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
    def __init__(self):
        super().__init__()
        self.setSingleStep(5)
        self.setAlignment(Qt.AlignRight)
        self.setFixedWidth(60)
