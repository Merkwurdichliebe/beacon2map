'''
Helper module for beacon2map, defining custom UI widgets.
'''
from beacon2map.locations import Location
import logging

from beacon2map.gridpoint import GridPoint
from PySide6.QtGui import QFont
from PySide6.QtCore import QPropertyAnimation, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QGraphicsOpacityEffect, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSpinBox, QTextEdit, QWidget
)

from beacon2map.config import config as cfg


logger = logging.getLogger(__name__)


class ToolbarFilterWidget(QWidget):
    '''A subclass of QWidget which holds several UI controls
    grouped together into a filter panel which can be added
    to the QToolBar as group.'''
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

        self.btn_reset_filters = QPushButton('Reset Filters')
        layout.addWidget(self.btn_reset_filters)

        self.setLayout(layout)

    def reset(self):
        '''Reset all checkboxes to 'checked' status.'''
        self.is_being_redrawn = True
        for cb in self.category_checkbox.values():
            cb.setChecked(True)
        self.checkbox_include_done.setChecked(True)
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

        self.gridpoint = None
        self.is_being_redrawn = False

        # Inspector layout

        layout = QGridLayout()
        layout.setRowMinimumHeight(0, 40)

        # Grid Row 0

        lbl = QLabel('Location Properties')
        lbl.setFont(QFont('Helvetica Neue', 18, QFont.Bold))
        layout.addWidget(lbl, 0, 0, 1, 6)

        # Grid Row 1

        layout.addWidget(QLabel('Name'), 1, 0)

        field = QLineEdit() 
        field.setMaxLength(40)
        layout.addWidget(field, 1, 1, 1, 5)
        self._edit_name = field

        # Grid Row 2

        layout.addWidget(QLabel('Distance'), 2, 0)
        field = QSpinBox()
        field.setAlignment(Qt.AlignRight)
        field.setMinimum(0)
        field.setMaximum(3000)
        layout.addWidget(field, 2, 1)
        self._edit_distance = field

        layout.addWidget(QLabel('Bearing'), 2, 2)
        field = QSpinBox()
        field.setAlignment(Qt.AlignRight)
        field.setMinimum(0)
        field.setMaximum(360)
        layout.addWidget(field, 2, 3)
        self._edit_bearing = field

        layout.addWidget(QLabel('Depth'), 2, 4)
        field = QSpinBox()
        field.setAlignment(Qt.AlignRight)
        field.setMinimum(-500)
        field.setMaximum(3000)
        layout.addWidget(field, 2, 5)
        self._edit_depth = field

        # Grid Row 3

        field = QComboBox()
        field.insertItems(0, cfg.categories.keys())
        layout.addWidget(field, 3, 0, 1, 2)
        self._edit_category = field

        layout.addWidget(QLabel('Heading'), 3, 2)
        field = QLabel()
        layout.addWidget(field, 3, 3, 1, 1)
        self._lbl_reciprocal = field

        field = QCheckBox('Done')
        layout.addWidget(field, 3, 4, 1, 2)
        self._edit_done = field

        # Grid Row 4

        field = QTextEdit()
        field.setAcceptRichText(False)
        layout.addWidget(field, 4, 0, 1, 6)
        self._edit_description = field

        # Grid Row 6

        field = QLabel()
        layout.addWidget(field, 5, 0, 1, 6)
        self._lbl_message = field

        # Grid Row 6

        field = QPushButton('Update')
        field.setDefault(True)
        field.clicked.connect(self._value_changed)
        layout.addWidget(field, 6, 2, 1, 2)
        self._btn_update = field

        # Setup fade-in/out animation

        self.opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity)
        self.opacity.setOpacity(0)
        self.visible = False

        self.anim_opacity = QPropertyAnimation(self.opacity, b'opacity')
        self.anim_opacity.setDuration(150)
        self.anim_opacity.finished.connect(self.anim_opacity_finished)

        # Finalise

        self.setStyleSheet(cfg.css['inspector'])
        self.setLayout(layout)
        self.move_into_position()

    def show(self, gridpoint: GridPoint = None):
        '''Override show() to allow passing a Gridpoint object.'''
        # We are updating the inspector so we set a flag
        # The flag is checked in _value_changed to avoid early modifications
        # to the source data
        self.is_being_redrawn = True

        # If a Gridpoint has been passed, display its properties
        if gridpoint is not None:
            self.gridpoint = gridpoint
            self.update_values_from(gridpoint.source)

        self._edit_distance.setFocus()

        # Position the inspector correctly if the Main Window
        # has been resized while the inspector was hidden
        if self.visibleRegion().isEmpty():
            self.move_into_position()

        # Fade-in effect
        if self.visible is False:
            self.anim_opacity.setStartValue(0)
            self.anim_opacity.setEndValue(1)
            self.anim_opacity.start()
        self.visible = True

        # Wrap-up
        self.is_being_redrawn = False
        return super().show()

    def hide(self):
        '''Override hide() to start the fade-out animation.'''
        if self.visible is True:
            self.anim_opacity.setStartValue(1)
            self.anim_opacity.setEndValue(0)
            self.anim_opacity.start()
        self.visible = False

    def anim_opacity_finished(self):
        '''Hide the widget when the opacity animation has finished.'''
        if self.opacity.opacity() == 0:
            return super().hide()

    def move_into_position(self):
        self.move(self.parentWidget().frameGeometry().width() - 390, 80)

    def update_values_from(self, loc: Location):
        self._edit_name.setText(loc.name)
        self._edit_distance.setValue(loc.distance)
        self._edit_bearing.setValue(loc.bearing)
        self._lbl_reciprocal.setText(str((self._edit_bearing.value()-180)%360))
        self._edit_depth.setValue(loc.depth)
        self._edit_category.setCurrentText(str(loc.category))
        self._edit_description.setText(str(loc.description or ''))
        self._edit_done.setChecked(loc.done)

    def _value_changed(self):
        if self.is_being_redrawn:
            return
        else:
            self.update_source_data()

    def update_source_data(self):
        '''Update the source object to reflect the values in the inspector.'''

        try:
            logger.debug(self._edit_distance.value())
            logger.debug(self._edit_bearing.value())
            logger.debug(self._edit_depth.value())
            self.gridpoint.source.set_distance_and_depth(
                self._edit_distance.value(),
                self._edit_depth.value()
            )
        except ValueError:
            msg = 'Invalid distance & depth values.'
            self._lbl_message.setStyleSheet('QLabel {color: orange}')
            self._lbl_message.setText(msg)
        else:
            if self._lbl_message.text():
                self._lbl_message.clear()
        self.gridpoint.source.bearing = self._edit_bearing.value()
        self.gridpoint.source.name = self._edit_name.text()
        self.gridpoint.source.category = self._edit_category.currentText()

        desc = self._edit_description.toPlainText()
        if desc == '':
            self.gridpoint.source.description = None
        else:
            self.gridpoint.source.description = desc

        self.gridpoint.source.done = self._edit_done.isChecked()

        self.update_values_from(self.gridpoint.source)
        logger.debug('Inspector : Updated Location : %s.', self.gridpoint.source)

        # Emit the Signal(Gridpoint)
        # This is connected to the scene's update_gridpoint_from_source()
        self.inspector_value_changed.emit(self.gridpoint)
