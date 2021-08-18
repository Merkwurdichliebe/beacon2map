#!/usr/bin/env python

'''
Helper module for beacon2map, defining custom UI widgets.
'''

import logging

from PySide6.QtGui import QFont
from PySide6.QtCore import QPropertyAnimation, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QGraphicsOpacityEffect, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton, QSpinBox,
    QTextEdit, QWidget
)

from gridpoint import GridPoint
from location import Location
from utility import logit
from config import config as cfg


logger = logging.getLogger(__name__)


class ToolbarFilterWidget(QWidget):
    '''
    A subclass of QWidget which holds several UI controls grouped together into
    a filter panel which can be added to the QToolBar as group.
    '''
    # Originally created in order to solve a vertical alignment problem
    # with the Reset Filter button.
    # https://forum.qt.io/topic/129244/qpushbutton-vertical-alignment-in-qtoolbar/5

    def __init__(self):
        super().__init__()

        self.is_being_redrawn = False

        layout = QHBoxLayout()

        self.category_checkbox = {}
        for cat in cfg.categories:
            self.category_checkbox[cat] = QCheckBox(cat.capitalize())
            layout.addWidget(self.category_checkbox[cat])

        self.checkbox_include_done = QCheckBox('Include Done')
        layout.addWidget(self.checkbox_include_done)

        self.checkbox_beacons_only = QCheckBox('Beacons')
        layout.addWidget(self.checkbox_beacons_only)

        self.btn_reset_filters = QPushButton('Reset Filters')
        layout.addWidget(self.btn_reset_filters)

        self.setLayout(layout)

    def reset(self):
        '''Reset all checkboxes to 'checked' status.'''
        self.is_being_redrawn = True
        for cb in self.category_checkbox.values():
            cb.setChecked(True)
        self.checkbox_include_done.setChecked(True)
        self.checkbox_beacons_only.setChecked(False)
        self.is_being_redrawn = False

    def set_exclusive_checkbox(self, clicked_cb):
        self.is_being_redrawn = True
        '''Check/uncheck current checkbox, set all others to opposite.'''
        for cb in self.category_checkbox.values():
            if cb is not clicked_cb:
                cb.setChecked(not clicked_cb.isChecked())
        self.is_being_redrawn = False


class DepthSpinBox(QSpinBox):
    '''Simple subclass of QSpinBox with customised parameters.'''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSingleStep(5)
        self.setAlignment(Qt.AlignRight)
        self.setFixedWidth(60)


class GridpointInspector(QGroupBox):
    '''
    Floating inspector for displaying and editing Gridpoint objects.
    '''
    inspector_value_changed = Signal(GridPoint)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(360, 280)
        self.setAutoFillBackground(True)
        self.setAlignment(Qt.AlignCenter)

        self._gridpoint = None
        self.is_animating = False

        # Inspector layout

        layout = QGridLayout()
        layout.setRowMinimumHeight(0, 40)

        # Grid Row 0

        lbl = QLabel('Location Properties')
        lbl.setFont(QFont('Helvetica Neue', 18, QFont.Bold))
        layout.addWidget(lbl, 0, 0, 1, 4)

        field = QCheckBox('Done')
        field.stateChanged.connect(self._value_changed)
        layout.addWidget(field, 0, 4, 1, 1)
        self._edit_done = field

        # Grid Row 1

        layout.addWidget(QLabel('Name'), 1, 0)
        field = QLineEdit()
        field.setMaxLength(40)
        field.editingFinished.connect(self._value_changed)
        layout.addWidget(field, 1, 1, 1, 3)
        self._edit_name = field

        field = QComboBox()
        field.insertItems(0, cfg.categories.keys())
        field.currentTextChanged.connect(self._value_changed)
        layout.addWidget(field, 1, 4, 1, 2)
        self._edit_category = field   

        # Grid Row 2

        layout.addWidget(QLabel('Distance'), 2, 0)
        field = QSpinBox()
        field.setAlignment(Qt.AlignRight)
        field.setMinimum(0)
        field.setMaximum(3000)
        layout.addWidget(field, 2, 1)
        self._edit_distance = field

        layout.addWidget(QLabel('Depth'), 2, 2)
        field = QSpinBox()
        field.setAlignment(Qt.AlignRight)
        field.setMinimum(-500)
        field.setMaximum(3000)
        layout.addWidget(field, 2, 3)
        self._edit_depth = field

        field = QPushButton('Update')
        field.setDefault(True)
        field.clicked.connect(self._update_distance_and_depth)
        layout.addWidget(field, 2, 4, 1, 2)
        self._btn_update = field

        # Grid Row 3

        layout.addWidget(QLabel('Bearing'), 3, 0)
        field = QSpinBox()
        field.setAlignment(Qt.AlignRight)
        field.setMinimum(0)
        field.setMaximum(359)
        field.setWrapping(True)
        field.valueChanged.connect(self._value_changed)
        layout.addWidget(field, 3, 1)
        self._edit_bearing = field

        layout.addWidget(QLabel('Heading'), 3, 2)
        field = QLabel()
        layout.addWidget(field, 3, 3, 1, 1)
        self._lbl_reciprocal = field     

        field = QCheckBox('Beacon')
        field.stateChanged.connect(self._value_changed)
        layout.addWidget(field, 3, 4, 1, 1)
        self._edit_beacon = field

        # Grid Row 4

        # Description Text Box
        field = QTextEdit()
        field.setAcceptRichText(False)
        field.textChanged.connect(self._value_changed)
        layout.addWidget(field, 4, 0, 1, 6)
        self._edit_description = field

        # Grid Row 5

        # Message placeholder
        field = QLabel()
        layout.addWidget(field, 5, 0, 1, 6)
        self._lbl_message = field

        # Setup fade-in/out animation

        self.opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity)

        self.anim_opacity = QPropertyAnimation(self.opacity, b'opacity')
        self.anim_opacity.setDuration(150)
        self.anim_opacity.finished.connect(self.anim_opacity_finished)

        # Finalise

        self.setStyleSheet(cfg.css['inspector'])
        self.setLayout(layout)
        self.move_into_position()
        self.hide()

    def selection_changed(self, items):
        if items:
            if isinstance(items[0], GridPoint):
                self.gridpoint = items[0]
                self.show()
                self._edit_distance.setFocus()
                self._edit_distance.selectAll()

        else:
            self.hide()

    def showEvent(self, event):
        logger.debug(f'{self.is_animating=}')
        if not self.is_animating:
            self.is_animating = True
            visible = True
            self.anim_opacity.setStartValue(int(not visible))
            self.anim_opacity.setEndValue(int(visible))
            self.anim_opacity.start()

        # Position the inspector correctly if the Main Window
        # has been resized while the inspector was hidden
        if self.visibleRegion().isEmpty():
            self.move_into_position()

    def hideEvent(self, event):
        logger.debug(f'{self.is_animating=}')
        if not self.is_animating:
            self.is_animating = True
            self.setVisible(True)
            visible = False
            self.anim_opacity.setStartValue(int(not visible))
            self.anim_opacity.setEndValue(int(visible))
            self.anim_opacity.start()

    def anim_opacity_finished(self):
        '''Hide the widget when the opacity animation has finished.'''
        super().setVisible(bool(self.opacity.opacity()))
        self.is_animating = False
        logger.debug(f'anim_opacity_finished: opacity={self.opacity.opacity()}')

    def move_into_position(self):
        self.move(self.parentWidget().frameGeometry().width() - 390, 80)

    def update_values(self):
        loc = self.gridpoint.source
        self._edit_name.setText(loc.name)
        self._edit_distance.setValue(loc.distance)
        self._edit_bearing.setValue(loc.bearing)
        self._lbl_reciprocal.setText(
            str((self._edit_bearing.value()-180) % 360))
        self._edit_depth.setValue(loc.depth)
        self._edit_category.setCurrentText(str(loc.category))
        self._edit_description.setText(str(loc.description or ''))
        self._edit_done.setChecked(loc.done)
        self._edit_beacon.setChecked(loc.beacon)

        # Align the name to the left if too long
        self._edit_name.home(True)
        self._edit_name.setSelection(0, 0)

    def _value_changed(self):
        '''SLOT for Inspector controls.'''
        if self.is_animating:
            return
        else:
            self.update_source_data()

    def update_source_data(self):
        '''
        Update the source object to reflect Inspector fields:
        name, bearing, category, description, done
        '''
        self.gridpoint.source.bearing = self._edit_bearing.value()
        self.gridpoint.source.name = self._edit_name.text()
        self.gridpoint.source.category = self._edit_category.currentText()

        desc = self._edit_description.toPlainText()
        if desc == '':
            self.gridpoint.source.description = None
        else:
            self.gridpoint.source.description = desc

        self.gridpoint.source.done = self._edit_done.isChecked()
        self.gridpoint.source.beacon = self._edit_beacon.isChecked()

        # Update the reciprocal heading QLabel
        self._lbl_reciprocal.setText(
            str((self._edit_bearing.value()-180) % 360))

        logger.debug(
            'Inspector : Updated Location : %s.', self.gridpoint.source)

        # Emit the Signal(Gridpoint)
        # This is connected to the scene's update_gridpoint_from_source()
        self.inspector_value_changed.emit(self.gridpoint)

    def _update_distance_and_depth(self):
        '''
        Update the source object to reflect Inspector fields after validation:
        distance, depth
        '''
        try:
            self.gridpoint.source.set_distance_and_depth(
                self._edit_distance.value(),
                self._edit_depth.value()
            )
        except ValueError:
            self._lbl_message.setStyleSheet('QLabel {color: orange}')
            self._lbl_message.setText('Invalid distance & depth values.')
        else:
            if self._lbl_message.text():
                self._lbl_message.clear()
            logger.debug(
                'Inspector : Updated distance and depth '
                f'for {self.gridpoint.source}.')

            # Emit the Signal(Gridpoint)
            # This is connected to the scene's update_gridpoint_from_source()
            self.inspector_value_changed.emit(self.gridpoint)

    @property
    def gridpoint(self):
        return self._gridpoint

    @gridpoint.setter
    def gridpoint(self, value):
        assert isinstance(value, GridPoint)
        self._gridpoint = value
        self.update_values()
