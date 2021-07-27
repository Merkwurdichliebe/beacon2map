#!/usr/bin/env python

"""
beacon2map creates a visual map based on marker locations read from a CSV file.
The markers hold names and descriptions and are based on
readings of distance, depth and bearing to a central reference beacon.

This app was designed as an exploration aid for the video game Subnautica.

Requirements: Qt6 and Pandas
"""

__author__ = "Tal Zana"
__copyright__ = "Copyright 2021"
__license__ = "GPL"
__version__ = "1.0"

import sys
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QIcon
from ui.mainwindow import MainWindow

if os.path.isfile('configmine.py'):
    import configmine as config
else:
    import config


def main():
    app = QApplication([])
    app.setWindowIcon(QIcon(QPixmap(config.icon['app'])))
    window = MainWindow()
    window.resize(config.window_width, config.window_height)
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()

# TODO Handle file not found
# TODO Fix zoom code when fast zooming out
# TODO File selection form
# TODO Marker type checkboxes
