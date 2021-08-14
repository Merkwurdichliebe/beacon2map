import logging

from PySide6.QtCore import QSize, QTimer, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QWidget
from PySide6.QtGui import QAction, QGuiApplication, QPixmap

from beacon2map.gridpoint import GridPoint
from beacon2map.locations import LocationMap
from beacon2map.sceneview import MapScene, MapView, SceneFilter
from beacon2map.widgets import (
    ToolbarFilterWidget, GridpointInspector, DepthSpinBox)
from beacon2map.config import config as cfg

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    '''Main Window for the application.
    Used to set up menus, toolbar and status bar behavior.'''

    def __init__(self, app):
        super().__init__()

        self.app = app
        self.app.main_window = self
        self.inspector = None

        assert isinstance(self.app.locationmap, LocationMap)

        logger.debug('Main Window init start.')

        # General window settings

        self.setWindowTitle('Subnautica Map')
        self.statusBar().setEnabled(True)
        self.resize(cfg.window_width, cfg.window_height)
        self.setMinimumSize(1200, 500)
        self.center_window()

        # We set the central widget but don't initialize it yet.
        # This allows the status bar to update properly,
        # after the window has been constructed.
        self.setCentralWidget(MainWidget())

        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self._create_inspector()

        self.populate_scene()

        logger.debug('Main Window init end.')

    def center_window(self):
        '''Center the window on the primary monitor.'''
        qt_rect = self.frameGeometry()
        center = QGuiApplication.primaryScreen().availableGeometry().center()
        qt_rect.moveCenter(center)
        self.move(qt_rect.topLeft())

    def _create_actions(self):
        '''Define and connect QAction objects
        for the menus and keyboard shortcuts.'''

        self.act_reload = QAction('&Reload CSV File', self)
        self.act_reload.setIcon(QPixmap(cfg.icon['reload']))
        self.act_reload.setShortcut(Qt.CTRL + Qt.Key_R)
        self.act_reload.setStatusTip('Reload CSV File')
        self.act_reload.setMenuRole(QAction.NoRole)
        self.act_reload.triggered.connect(self.populate_scene)

        self.act_reset_zoom = QAction('&Reset Zoom', self)
        self.act_reset_zoom.setIcon(QPixmap(cfg.icon['reset_zoom']))
        self.act_reset_zoom.setShortcut(Qt.Key_Space)
        self.act_reset_zoom.setStatusTip('Reset Zoom')
        self.act_reset_zoom.setMenuRole(QAction.NoRole)
        self.act_reset_zoom.triggered.connect(self.centralWidget().reset_zoom)

        self.act_toggle_grid = QAction('Toggle &Grid', self)
        self.act_toggle_grid.setIcon(QPixmap(cfg.icon['grid']))
        self.act_toggle_grid.setShortcut(Qt.CTRL + Qt.Key_G)
        self.act_toggle_grid.setStatusTip('Toggle Grid')
        self.act_toggle_grid.setMenuRole(QAction.NoRole)
        self.act_toggle_grid.triggered.connect(self.centralWidget().toggle_grid)

        self.act_save = QAction('&Save', self)
        self.act_save.setIcon(QPixmap(cfg.icon['grid']))
        self.act_save.setShortcut(Qt.CTRL + Qt.Key_S)
        self.act_save.setStatusTip('Save')
        self.act_save.setMenuRole(QAction.NoRole)
        self.act_save.triggered.connect(self.app.save)

        self.act_delete_location = QAction('&Delete Location', self)
        self.act_delete_location.setShortcut(Qt.Key_Backspace)
        self.act_delete_location.triggered.connect(self.delete_location)
        self.addAction(self.act_delete_location)

    def _create_menus(self):
        menubar = self.menuBar()
        menu_file = menubar.addMenu('&File')
        menu_file.addAction(self.act_reload)
        menu_file.addAction(self.act_save)

        menu_view = menubar.addMenu('&View')
        menu_view.addAction(self.act_reset_zoom)
        menu_view.addAction(self.act_toggle_grid)

    def _create_toolbar(self):

        # Toolbar buttons

        toolbar = self.addToolBar('Main')
        toolbar.setIconSize(QSize(25, 25))
        toolbar.setMovable(False)
        toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        toolbar.addAction(self.act_reload)
        toolbar.addAction(self.act_save)
        toolbar.addAction(self.act_reset_zoom)
        toolbar.addAction(self.act_toggle_grid)

        toolbar.addSeparator()

        # Min & Max Depth SpinBoxes

        toolbar.addWidget(QLabel(
            'Min depth', self, styleSheet='QLabel {padding: 0 5}'))
        self.spin_min = DepthSpinBox(self)
        toolbar.addWidget(self.spin_min)

        toolbar.addWidget(QLabel(
            'Max depth', self, styleSheet='QLabel {padding: 0 5}'))
        self.spin_max = DepthSpinBox(self)
        toolbar.addWidget(self.spin_max)

        self.spin_min.valueChanged.connect(self.spin_value_changed)
        self.spin_max.valueChanged.connect(self.spin_value_changed)

        # Category Filter Widget

        self.filter_widget = ToolbarFilterWidget()
        toolbar.addWidget(self.filter_widget)

        # Connect Filter Widget Signals

        self.filter_widget.checkbox_include_done.stateChanged.connect(self.set_filter)
        self.filter_widget.btn_reset_filters.clicked.connect(self.reset_filters)

        # We need cb as a *second* argument in the lambda expression
        # https://stackoverflow.com/questions/35819538/using-lambda-expression-to-connect-slots-in-pyqt
        for checkbox in self.filter_widget.category_checkbox.values():
            checkbox.stateChanged.connect(
                lambda state, cb=checkbox: self.category_checkbox_clicked(cb))

    def _create_inspector(self):
        self.inspector = GridpointInspector(self)
        self.inspector.hide()
        self.inspector.inspector_value_changed.connect(
            self.centralWidget().scene.inspector_value_changed)

    def populate_scene(self):
        '''Initialize the central widget with the app location data.
        Also serves as a SLOT connected to QAction act_reload.
        '''
        try:
            self.centralWidget().scene.initialize(self.app.locationmap)
        except RuntimeError as e:
            msg = f'\nMain Window : Scene initialisation failed {e}.'
            raise RuntimeError(msg) from e

    def selection_changed(self, item: GridPoint):
        '''Slot called whenever scene.selectionChanged Signal is emitted.'''
        # If an item has been selected, display the Inspector.
        if item:
            assert isinstance(item[0], GridPoint)
            gp = item[0]
            self.inspector.show(gp)
            logger.debug('Gridpoint selected: %s', gp)
        else:
            self.inspector.hide()
            logger.debug('No selection')

    def scene_finished_loading(self):
        '''SLOT called whenever scene.gridpoints_loaded Signal is emitted.'''

        # Display message in the Status Bar
        msg = f'Loaded {self.app.locationmap.size} locations from file.'
        self.statusBar().showMessage(msg)
        QTimer.singleShot(4000, self.clear_status_bar)

        # Reset the toolbar filters
        self.reset_filters()

    def clear_status_bar(self):
        self.statusBar().clearMessage()

    def reset_filters(self):
        min_depth = self.app.locationmap.extents.min_z
        max_depth = self.app.locationmap.extents.max_z
        self.spin_min.setMinimum(min_depth)
        self.spin_min.setMaximum(max_depth)
        self.spin_max.setMinimum(min_depth)
        self.spin_max.setMaximum(max_depth)
        self.spin_min.setValue(min_depth)
        self.spin_max.setValue(max_depth)
        self.filter_widget.reset()

    def spin_value_changed(self):
        # Don't let the min and max value invert positions
        self.spin_min.setMaximum(self.spin_max.value())
        self.spin_max.setMinimum(self.spin_min.value())
        self.set_filter()

    def category_checkbox_clicked(self, clicked_cb):
        logger.debug(f'Category checkbox changed {clicked_cb}.')
        # Use Command Key for exclusive checkbox behavior
        if (self.is_command_key_held() and
                not self.filter_widget.is_being_redrawn):
            self.filter_widget.set_exclusive_checkbox(clicked_cb)
        self.set_filter()

    def set_filter(self):
        categories = []
        for k, v in self.filter_widget.category_checkbox.items():
            if v.isChecked():
                categories.append(k)
        done = self.filter_widget.checkbox_include_done.isChecked()
        filt = SceneFilter(
            min=self.spin_min.value(),
            max=self.spin_max.value(),
            categories=categories,
            include_done=done)
        logger.debug(f'Setting filter : {filt}.')
        self.centralWidget().scene.filter(filt)

    def delete_location(self):
        selection = self.centralWidget().scene.selectedItems()
        if selection:
            self.app.delete_location(selection[0].source)
            # TODO for now we only delete the first item in a multiple selection

    @staticmethod
    def is_command_key_held():
        return QGuiApplication.keyboardModifiers() == Qt.ControlModifier

    def resizeEvent(self, event):
        if self.inspector.isVisible():
            self.inspector.move_into_position()
        return super().resizeEvent(event)


class MainWidget(QWidget):
    '''Main map widget. Sets up the Scene and View.'''

    def __init__(self):
        super().__init__()

        # Setup QGraphicsScene
        self.scene = MapScene()
        self.scene.selectionChanged.connect(
            lambda: self.parentWidget().selection_changed(self.scene.selectedItems()))
        self.scene.gridpoints_loaded.connect(
            lambda: self.parentWidget().scene_finished_loading())

        # Setup QGraphicsView & layout
        self.view = MapView(self.scene)
        layout = QHBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

    def reset_zoom(self):
        self.view.reset()

    def toggle_grid(self):
        self.scene.set_visible_grid()
