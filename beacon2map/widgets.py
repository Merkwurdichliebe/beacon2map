'''
Helper module for beacon2map, defining custom UI widgets.
'''


from beacon2map.gridpoint import GridPoint
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QTextEdit, QVBoxLayout, QWidget
)

from beacon2map.config import config as cfg


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
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(340, 200)
        self.setAutoFillBackground(True)
        self.setTitle('Location Properties')
        self.setAlignment(Qt.AlignCenter)

        layout = QGridLayout()

        # Grid Row 1

        layout.addWidget(QLabel('Name'), 0, 0)

        self._edit_name = QLineEdit() 
        layout.addWidget(self._edit_name, 0, 1, 1, 5)

        # Grid Row 2

        layout.addWidget(QLabel('Distance'), 1, 0)
        self._edit_distance = QLineEdit()
        self._edit_distance.setAlignment(Qt.AlignRight)
        layout.addWidget(self._edit_distance, 1, 1)

        layout.addWidget(QLabel('Bearing'), 1, 2)
        self._edit_bearing = QLineEdit()
        self._edit_bearing.setAlignment(Qt.AlignRight)
        layout.addWidget(self._edit_bearing, 1, 3)

        layout.addWidget(QLabel('Depth'), 1, 4)
        self._edit_depth = QLineEdit()
        self._edit_depth.setAlignment(Qt.AlignRight)
        layout.addWidget(self._edit_depth, 1, 5)

        # Grid Row 3

        self._edit_category = QComboBox()
        self._edit_category.insertItems(0, cfg.categories.keys())
        layout.addWidget(self._edit_category, 2, 0, 1, 4)

        self._edit_done = QCheckBox('Done')
        layout.addWidget(self._edit_done, 2, 4, 1, 2)

        # Grid Row 4

        self._edit_description = QTextEdit()
        layout.addWidget(self._edit_description, 3, 0, 3, 6)

        self.setLayout(layout)

        self.move_into_position()

    def show(self, gridpoint=None):
        if gridpoint is not None:
            self._edit_name.setText(gridpoint.name)
            self._edit_distance.setText(str(gridpoint.distance))
            self._edit_bearing.setText(str(gridpoint.bearing))
            self._edit_depth.setText(str(gridpoint.depth))
            self._edit_category.setCurrentText(str(gridpoint.category))
            self._edit_description.setText(str(gridpoint.description or ''))
        super().show()

    def move_into_position(self):
        self.move(self.parentWidget().frameGeometry().width() - 370, 80)
