from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout, QPushButton, QCheckBox
from PySide6.QtGui import QFont

FONT_FAMILY = 'Helvetica'


class UIPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title label
        lbl_title = QLabel('Subnautica Map')
        lbl_title.setFixedWidth(150)
        lbl_title.setFont(QFont(FONT_FAMILY, 16, QFont.Bold))
        layout.addWidget(lbl_title)

        # Stats label
        self.lbl_stats = QLabel()
        layout.addWidget(self.lbl_stats)

        # Reload button
        self.btn_reload = QPushButton('Reload')
        layout.addWidget(self.btn_reload)

        # Show Grid checkbox
        cb_grid = QCheckBox('Show Grid')
        cb_grid.toggle()
        # cb_grid.stateChanged.connect(self.scene.setVisibleGrid)
        layout.addWidget(cb_grid)

        layout.addSpacing(16)

        self.marker_box = UIMarkerBox()
        layout.addWidget(self.marker_box)

        layout.addStretch()

    # Update the stats label
    def update_stats(self, scene):
        text = f'{len(scene.markers)} markers loaded'
        self.lbl_stats.setText(text)


class UIMarkerBox(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Marker title label
        title = QLabel('Marker')
        title.setFont(QFont(FONT_FAMILY, 14, QFont.Bold))
        layout.addWidget(title)

        # Marker name label
        self.name = QLabel()
        layout.addWidget(self.name)

        # Marker description label
        self.desc = QLabel()
        self.desc.setWordWrap(True)
        self.desc.setFixedWidth(150)
        layout.addWidget(self.desc)

    def update(self, scene):
        if scene.selectedItems():
            marker = scene.selectedItems()[0]
            self.name.setText(marker.label)
            if marker.desc:
                self.desc.setText('> ' + marker.desc)
            else:
                self.desc.clear()
            self.show()
        else:
            self.hide()        
        
