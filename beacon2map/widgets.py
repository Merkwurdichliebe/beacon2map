'''
Helper module for beacon2map, defining custom UI widgets.
'''
import logging

from beacon2map.gridpoint import GridPoint
from PySide6.QtGui import QFont, QIntValidator
from PySide6.QtCore import QPropertyAnimation, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QGraphicsOpacityEffect, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSpinBox, QTextEdit, QWidget
)

from beacon2map.config import config as cfg


# Set up logging
logger = logging.getLogger('b2a' + __name__)


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

        layout.addWidget(QLabel('Min depth', self, styleSheet='QLabel {padding: 0 5}'))

        self.spin_min = DepthSpinBox(self)
        layout.addWidget(self.spin_min)

        layout.addWidget(QLabel('Max depth', self, styleSheet='QLabel {padding: 0 5}'))

        self.spin_max = DepthSpinBox(self)
        layout.addWidget(self.spin_max)

        self.category_checkbox = {}
        for cat in cfg.categories:
            self.category_checkbox[cat] = QCheckBox(cat.capitalize())
            layout.addWidget(self.category_checkbox[cat])

        self.checkbox_include_done = QCheckBox('Include Done')
        layout.addWidget(self.checkbox_include_done)

        self.btn_reset_filters = QPushButton('Reset Filters')
        layout.addWidget(self.btn_reset_filters)

        self.setLayout(layout)


class DepthSpinBox(QSpinBox):
    '''Simple subclass of QSpinBox with customised parameters.'''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSingleStep(5)
        self.setAlignment(Qt.AlignRight)
        self.setFixedWidth(60)


class GridpointInspector(QGroupBox):
    inspector_value_changed = Signal(GridPoint)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(340, 250)
        self.setAutoFillBackground(True)
        self.setAlignment(Qt.AlignCenter)

        self.gridpoint = None
        self.is_being_redrawn = False

        layout = QGridLayout()
        layout.setRowMinimumHeight(0, 40)

        # Grid Row 0

        lbl = QLabel('Location Properties')
        lbl.setFont(QFont('Helvetica', 18, QFont.Bold))
        layout.addWidget(lbl, 0, 0, 1, 6)

        # Grid Row 1

        layout.addWidget(QLabel('Name'), 1, 0)

        self._edit_name = QLineEdit() 
        self._edit_name.setMaxLength(40)
        self._edit_name.editingFinished.connect(self._value_changed)
        layout.addWidget(self._edit_name, 1, 1, 1, 5)

        # Grid Row 2

        layout.addWidget(QLabel('Distance'), 2, 0)
        self._edit_distance = QSpinBox()
        self._edit_distance.setAlignment(Qt.AlignRight)
        self._edit_distance.setMinimum(0)
        self._edit_distance.setMaximum(3000)
        self._edit_distance.valueChanged.connect(self._value_changed)
        layout.addWidget(self._edit_distance, 2, 1)

        layout.addWidget(QLabel('Bearing'), 2, 2)
        self._edit_bearing = QSpinBox()
        self._edit_bearing.setAlignment(Qt.AlignRight)
        self._edit_bearing.setMinimum(0)
        self._edit_bearing.setMaximum(360)
        self._edit_bearing.valueChanged.connect(self._value_changed)
        layout.addWidget(self._edit_bearing, 2, 3)

        layout.addWidget(QLabel('Depth'), 2, 4)
        self._edit_depth = QSpinBox()
        self._edit_depth.setAlignment(Qt.AlignRight)
        self._edit_depth.setMinimum(-500)
        self._edit_depth.setMaximum(3000)
        self._edit_depth.valueChanged.connect(self._value_changed)
        layout.addWidget(self._edit_depth, 2, 5)

        # Grid Row 3

        self._edit_category = QComboBox()
        self._edit_category.insertItems(0, cfg.categories.keys())
        self._edit_category.currentTextChanged.connect(self._value_changed)
        layout.addWidget(self._edit_category, 3, 0, 1, 4)

        self._edit_done = QCheckBox('Done')
        self._edit_done.stateChanged.connect(self._value_changed)
        layout.addWidget(self._edit_done, 3, 4, 1, 2)

        # Grid Row 4

        self._edit_description = QTextEdit()
        self._edit_description.textChanged.connect(self._value_changed)
        layout.addWidget(self._edit_description, 4, 0, 1, 6)

        # Setup animation

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

    def show(self, gridpoint=None):
        self.is_being_redrawn = True
        if gridpoint is not None:
            self.gridpoint = gridpoint
            loc = self.gridpoint.source
            self._edit_name.setText(loc.name)
            self._edit_distance.setValue(loc.distance)
            self._edit_bearing.setValue(loc.bearing)
            self._edit_depth.setValue(loc.depth)
            self._edit_category.setCurrentText(str(loc.category))
            self._edit_description.setText(str(loc.description or ''))

        # Position the inspector correctly if the Main Window
        # has been resized while the inspector was hidden
        if self.visibleRegion().isEmpty():
            self.move_into_position()

        if self.visible is False:
            self.anim_opacity.setStartValue(0)
            self.anim_opacity.setEndValue(1)
            self.anim_opacity.start()
        self.visible = True
        self.is_being_redrawn = False
        return super().show()

    def hide(self):
        if self.visible is True:
            self.anim_opacity.setStartValue(1)
            self.anim_opacity.setEndValue(0)
            self.anim_opacity.start()
        self.visible = False

    def anim_opacity_finished(self):
        if self.opacity.opacity() == 0:
            return super().hide()

    def move_into_position(self):
        self.move(self.parentWidget().frameGeometry().width() - 370, 80)

    def _value_changed(self):
        if self.is_being_redrawn:
            return
        else:
            self.update_source_data()

    def update_source_data(self):
        self.gridpoint.source.name = self._edit_name.text()
        self.gridpoint.source.distance = self._edit_distance.value()
        self.gridpoint.source.bearing = self._edit_bearing.value()
        self.gridpoint.source.depth = self._edit_depth.value()
        self.gridpoint.source.category = self._edit_category.currentText()

        desc = self._edit_description.toPlainText()
        if desc == '':
            self.gridpoint.source.description = None
        else:
            self.gridpoint.source.description = desc

        self.gridpoint.source.done = self._edit_done.isChecked()
        self.inspector_value_changed.emit(self.gridpoint)
