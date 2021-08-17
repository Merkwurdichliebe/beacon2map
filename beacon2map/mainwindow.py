#!/usr/bin/env python

import logging

from PySide6.QtCore import QEvent, QSize, QTimer, Qt
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QRadioButton, QWidget)
from PySide6.QtGui import QAction, QGuiApplication, QPixmap, QCloseEvent

from gridpoint import GridPoint
from location import LocationMap
from sceneview import MapScene, MapView, SceneFilter
from widgets import (
    ToolbarFilterWidget, GridpointInspector, DepthSpinBox)

from config import config as cfg
from utility import logit

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    '''
    Main Window for the application. Used to set up menus, toolbar and status
    bar behavior.
    '''

    def __init__(self, app):
        super().__init__()

        self.has_finished_loading = False
        self.app = app
        self.inspector = None

        assert isinstance(self.app.map, LocationMap)

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

        self.has_finished_loading = True
        logger.info('Main Window initialisation finished.')

    def center_window(self) -> None:
        '''Center the window on the primary monitor.'''
        qt_rect = self.frameGeometry()
        center = QGuiApplication.primaryScreen().availableGeometry().center()
        qt_rect.moveCenter(center)
        self.move(qt_rect.topLeft())

    def _create_actions(self) -> None:
        '''Define and connect QAction objects
        for the menus and keyboard shortcuts.'''

        self.act_reload = QAction('&Reload locations file', self)
        self.act_reload.setIcon(QPixmap(cfg.icon['reload']))
        self.act_reload.setShortcut(Qt.CTRL + Qt.Key_R)
        self.act_reload.setStatusTip('Reload locations file')
        self.act_reload.setMenuRole(QAction.NoRole)
        self.act_reload.triggered.connect(self.populate_scene)

        self.act_reset_zoom = QAction('&Reset Zoom', self)
        self.act_reset_zoom.setIcon(QPixmap(cfg.icon['reset_zoom']))
        self.act_reset_zoom.setShortcut(Qt.Key_Space)
        self.act_reset_zoom.setStatusTip('Reset Zoom')
        self.act_reset_zoom.setMenuRole(QAction.NoRole)
        self.act_reset_zoom.triggered.connect(self.reset_zoom)

        self.act_toggle_grid = QAction('Toggle &Grid', self)
        self.act_toggle_grid.setIcon(QPixmap(cfg.icon['grid']))
        self.act_toggle_grid.setShortcut(Qt.CTRL + Qt.Key_G)
        self.act_toggle_grid.setStatusTip('Toggle Grid')
        self.act_toggle_grid.setMenuRole(QAction.NoRole)
        self.act_toggle_grid.triggered.connect(self.toggle_grid)

        self.act_save = QAction('&Save', self)
        self.act_save.setIcon(QPixmap(cfg.icon['save']))
        self.act_save.setShortcut(Qt.CTRL + Qt.Key_S)
        self.act_save.setStatusTip('Save')
        self.act_save.setMenuRole(QAction.NoRole)
        self.act_save.triggered.connect(self.app.save)

        self.act_new_location = QAction('&Add Location', self)
        self.act_new_location.setIcon(QPixmap(cfg.icon['new']))
        self.act_new_location.setShortcut(Qt.CTRL + Qt.Key_N)
        self.act_new_location.setStatusTip('Add New Location ')
        self.act_new_location.setMenuRole(QAction.NoRole)
        self.act_new_location.triggered.connect(self.add_location)

        self.act_delete_location = QAction('&Delete Location', self)
        self.act_delete_location.setShortcut(Qt.Key_Backspace)
        self.act_delete_location.triggered.connect(self.delete_location)
        self.addAction(self.act_delete_location)

    def _create_menus(self) -> None:
        '''Create the application menus.'''
        menubar = self.menuBar()
        menu_file = menubar.addMenu('&File')
        menu_file.addAction(self.act_reload)
        menu_file.addAction(self.act_save)

        menu_edit = menubar.addMenu('&Edit')
        menu_edit.addAction(self.act_new_location)

        menu_view = menubar.addMenu('&View')
        menu_view.addAction(self.act_reset_zoom)
        menu_view.addAction(self.act_toggle_grid)

    def _create_toolbar(self) -> None:
        '''Create the application toolbar.'''

        # Toolbar buttons

        toolbar = self.addToolBar('Main')
        toolbar.setIconSize(QSize(25, 25))
        toolbar.setMovable(False)
        toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        toolbar.addAction(self.act_reload)
        toolbar.addAction(self.act_save)
        toolbar.addAction(self.act_reset_zoom)
        toolbar.addAction(self.act_toggle_grid)
        toolbar.addAction(self.act_new_location)

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

        self.filter_widget.checkbox_include_done.stateChanged.connect(
            self.set_filter)
        self.filter_widget.btn_reset_filters.clicked.connect(
            self.reset_filters)

        # We need cb as a *second* argument in the lambda expression
        # https://stackoverflow.com/questions/35819538/using-lambda-expression-to-connect-slots-in-pyqt
        for checkbox in self.filter_widget.category_checkbox.values():
            checkbox.stateChanged.connect(
                lambda state, cb=checkbox: self.category_checkbox_clicked(cb))

        # Color Scheme Radio Buttons

        toolbar.addWidget(QLabel('Color by'))

        self.radio_category = QRadioButton('Category')
        toolbar.addWidget(self.radio_category)
        self.radio_depth = QRadioButton('Depth')
        toolbar.addWidget(self.radio_depth)

        self.radio_category.setChecked(True)

        self.group = QButtonGroup()
        self.group.addButton(self.radio_category)
        self.group.addButton(self.radio_depth)
        self.group.buttonClicked.connect(self.color_scheme_changed)

    def _create_inspector(self) -> None:
        '''Create and hide the GridPoint Inspector.'''
        self.inspector = GridpointInspector(self)
        self.inspector.hide()
        self.inspector.inspector_value_changed.connect(
            self.centralWidget().scene.modify_gridpoint)
        self.inspector.inspector_value_changed.connect(
            self.scene_has_changed)

    def populate_scene(self) -> None:
        '''Initialize the central widget with the app location data.
        Also serves as a SLOT connected to QAction act_reload.
        '''
        assert self.app.map is not None
        try:
            self.centralWidget().scene.initialize(self.app.map)
        except RuntimeError as e:
            raise RuntimeError(
                f'Main Window : Scene initialisation failed {e}.') from e

    @logit
    def selection_changed(self, item: GridPoint):
        '''SLOT for scene.selectionChanged Signal.'''
        # If an item has been selected, display the Inspector.
        if item:
            assert isinstance(item[0], GridPoint)
            gp = item[0]
            self.inspector.show(gp)
        else:
            self.inspector.hide()

    def scene_finished_loading(self) -> None:
        '''SLOT for scene.finished_drawing_gridpoints Signal.'''

        # Display message in the Status Bar
        self.statusBar().showMessage(
            f'Loaded {self.app.map.size} locations from file.')
        QTimer.singleShot(4000, self.clear_status_bar)

        # Reset the toolbar filters
        self.reset_filters()

    def clear_status_bar(self) -> None:
        self.statusBar().clearMessage()

    def reset_filters(self) -> None:
        '''Reset toolbar to default values (i.e. all GridPoints visible).'''
        min_depth = self.app.map.extents.min_z
        max_depth = self.app.map.extents.max_z
        self.spin_min.setMinimum(min_depth)
        self.spin_min.setMaximum(max_depth)
        self.spin_max.setMinimum(min_depth)
        self.spin_max.setMaximum(max_depth)
        self.spin_min.setValue(min_depth)
        self.spin_max.setValue(max_depth)
        self.filter_widget.reset()

    def spin_value_changed(self) -> None:
        '''SLOT for toolbar depth spinboxes.'''
        # Don't let the min and max value invert positions
        self.spin_min.setMaximum(self.spin_max.value())
        self.spin_max.setMinimum(self.spin_min.value())
        self.set_filter()

    # @logit
    def category_checkbox_clicked(self, clicked_cb: QCheckBox) -> None:
        '''SLOT for clicked toolbar checkboxes.'''
        assert isinstance(clicked_cb, QCheckBox)
        # Use Command Key for exclusive checkbox behavior
        if (self.is_command_key_held() and
                not self.filter_widget.is_being_redrawn):
            self.filter_widget.set_exclusive_checkbox(clicked_cb)
        self.set_filter()

    def set_filter(self) -> None:
        '''Build the SceneFilter based on current toolbar values.'''
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
        self.centralWidget().scene.filter(filt)

    def color_scheme_changed(self, radio: QRadioButton):
        self.centralWidget().scene.set_color_scheme(radio.text().lower())

    def add_location(self) -> None:
        loc = self.app.add_location()
        gp = self.centralWidget().scene.add_gridpoint(loc)
        gp.setSelected(True)

    def delete_location(self) -> None:
        '''Delete selected Gridpoints and corresponding Locations.'''
        for item in self.centralWidget().scene.selectedItems():
            if isinstance(item, GridPoint):
                self.centralWidget().scene.delete_gridpoint(item)
                self.app.delete_location(item.source)

    @staticmethod
    def is_command_key_held() -> bool:
        return QGuiApplication.keyboardModifiers() == Qt.ControlModifier

    def resizeEvent(self, event) -> QEvent:
        '''Keep the Inspector in place if the window is resized.'''
        if self.inspector.isVisible():
            self.inspector.move_into_position()
        return super().resizeEvent(event)

    def reset_zoom(self) -> None:
        self.centralWidget().view.reset()

    def toggle_grid(self) -> None:
        self.centralWidget().scene.toggle_grid()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.app.data_has_changed:
            msgbox = QMessageBox()
            msgbox.setText('Save before quitting?')
            msgbox.setInformativeText('Changes will be lost otherwise.\n')
            msgbox.setStandardButtons(
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            reply = msgbox.exec()

            if reply == QMessageBox.Save:
                self.act_save.trigger()
            elif reply == QMessageBox.Cancel:
                event.ignore()
            else:
                event.accept()

        if event.isAccepted():
            logger.info('Quitting.')
            return super().closeEvent(event)

    def scene_has_changed(self):
        self.app.data_has_changed = True


class MainWidget(QWidget):
    '''Main map widget. Contains the Scene and View. Most of the work is done
    either in the parent MainWindow or in MapScene itself.'''

    def __init__(self):
        super().__init__()

        # Setup QGraphicsScene
        self.scene = MapScene()
        self.scene.selectionChanged.connect(
            lambda: self.parentWidget().selection_changed(
                self.scene.selectedItems()))
        self.scene.finished_drawing_gridpoints.connect(
            lambda: self.parentWidget().scene_finished_loading())

        # Setup QGraphicsView & layout
        self.view = MapView(self.scene)
        layout = QHBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)
