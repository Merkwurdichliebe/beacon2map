import logging

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QWidget
from PySide6.QtGui import QAction, QGuiApplication, QPixmap

from beacon2map.sceneview import MapScene, MapView
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

        if self.app.locationmap is not None:
            self.init()

    def init(self):
        logger.debug('Main Window init start.')

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
        qt_rect = self.frameGeometry()
        center = QGuiApplication.primaryScreen().availableGeometry().center()
        qt_rect.moveCenter(center)
        self.move(qt_rect.topLeft())

    def populate_scene(self):
        '''Initialize the central widget with the app location data.
        Also functions as a slot connected to the QAction act_reload.
        '''
        try:
            self.centralWidget().populate_scene(self.app.locationmap)
        except RuntimeError as e:
            msg = f'\nMain Window Populate scene failed {e}'
            raise RuntimeError(msg) from e

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

        # Command buttons

        toolbar = self.addToolBar('Main')
        toolbar.setIconSize(QSize(25, 25))
        toolbar.setMovable(False)
        toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        toolbar.addAction(self.act_reload)
        toolbar.addAction(self.act_save)
        toolbar.addAction(self.act_reset_zoom)
        toolbar.addAction(self.act_toggle_grid)

        toolbar.addSeparator()

        toolbar.addWidget(QLabel('Min depth', self, styleSheet='QLabel {padding: 0 5}'))

        self.spin_min = DepthSpinBox(self)
        toolbar.addWidget(self.spin_min)

        toolbar.addWidget(QLabel('Max depth', self, styleSheet='QLabel {padding: 0 5}'))

        self.spin_max = DepthSpinBox(self)
        toolbar.addWidget(self.spin_max)

        # Filter Widget

        self.filter_widget = ToolbarFilterWidget()
        toolbar.addWidget(self.filter_widget)

        # Connect Filter Widget Signals

        self.spin_min.valueChanged.connect(self.spin_value_changed)
        self.spin_max.valueChanged.connect(self.spin_value_changed)
        self.filter_widget.checkbox_include_done.stateChanged.connect(self.set_filter)
        self.filter_widget.btn_reset_filters.clicked.connect(self.reset_filters)
        for checkbox in self.filter_widget.category_checkbox.values():
            checkbox.stateChanged.connect(
                lambda state, cb=checkbox: self.category_checkbox_clicked(cb))

    def _create_inspector(self):
        self.inspector = GridpointInspector(self)
        self.inspector.hide()
        self.inspector.inspector_value_changed.connect(
            self.centralWidget().scene.inspector_value_changed)

    def selection_changed(self, item):
        '''Slot called whenever scene.selectionChanged Signal is emitted.'''

        # If an item has been selected, display the Inspector.
        if item:
            gp = item[0]
            logger.debug('Gridpoint selected: %s', gp)
            self.inspector.show(gp)
        else:
            logger.debug('No selection')
            self.inspector.hide()

    def scene_finished_loading(self, scene):
        '''Slot called whenever scene.gridpoints_loaded Signal is emitted.'''

        # Display the relevant message in the Status Bar
        msg = f'Loaded {len(scene.gridpoints)} locations.'
        self.statusBar().showMessage(msg)

        # Reset the depth spin boxes to min-max values
        self.reset_filters()

    def reset_filters(self):
        min_depth = self.app.locationmap.extents.min_z
        max_depth = self.app.locationmap.extents.max_z
        self.spin_min.setMinimum(min_depth)
        self.spin_min.setMaximum(max_depth)
        self.spin_max.setMinimum(min_depth)
        self.spin_max.setMaximum(max_depth)
        self.spin_min.setValue(min_depth)
        self.spin_max.setValue(max_depth)
        for cb in self.filter_widget.category_checkbox.values():
            cb.blockSignals(True)
            cb.setChecked(True)
            cb.blockSignals(False)
        self.filter_widget.checkbox_include_done.setChecked(True)
        self.set_filter()

    def spin_value_changed(self):
        # Don't let the min and max value invert positions
        self.spin_min.setMaximum(self.spin_max.value())
        self.spin_max.setMinimum(self.spin_min.value())
        self.set_filter()

    def category_checkbox_clicked(self, current_cb):
        # Use Command Key for exclusive checkbox behavior
        if self.is_command_key_held() and not self.filter_widget.is_being_redrawn:
            self.filter_widget.is_being_redrawn = True
            self.invert_category_filter(current_cb)
            self.filter_widget.is_being_redrawn = False
        self.set_filter()

    def invert_category_filter(self, current_cb):
        for cb in self.filter_widget.category_checkbox.values():
            if cb is not current_cb:
                cb.setChecked(not current_cb.isChecked())

    def set_filter(self):
        categories = []
        for k, v in self.filter_widget.category_checkbox.items():
            if v.isChecked():
                categories.append(k)
        done = self.filter_widget.checkbox_include_done.isChecked()
        filt = (
            self.spin_min.value(),
            self.spin_max.value(),
            categories,
            done
            )
        self.centralWidget().filter(filt)

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
            lambda: self.parentWidget().scene_finished_loading(self.scene))

        # Setup QGraphicsView & layout
        self.view = MapView(self.scene)
        layout = QHBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

    def reset_zoom(self):
        self.view.reset()

    def populate_scene(self, locmap):
        try:
            self.scene.initialize(locmap)
        except RuntimeError as e:
            msg = f'\nMainWidget Populate scene failed {e}'
            raise RuntimeError(msg) from e

    def toggle_grid(self):
        self.scene.set_visible_grid()

    def filter(self, filt):
        self.scene.filter(filt)
