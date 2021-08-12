'''
Helper module for beacon2map, defining custom UI widgets.
'''


from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QPushButton, QSpinBox, QWidget

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


