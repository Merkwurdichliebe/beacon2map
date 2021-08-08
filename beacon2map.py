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
import logging

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QIcon

from beacon2map.mainwindow import MainWindow
from beacon2map.locations import LocationMap

# Use local config file if present
if os.path.isfile('configmine.py'):
    import configmine as config
else:
    import config

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Beacon2Map(QApplication):
    '''Main application/controller object for beacon2map.'''
    def __init__(self):
        super().__init__()

        self._locationmap = None

    @property
    def locationmap(self):
        '''Create a LocationMap object from CSV file.
        This property reloads the file whenever its requested,
        to allow for data reload.
        '''
        self._locationmap = LocationMap(config.filename)
        logger.info('Beacon2Map: Locations loaded from %s', config.filename)
        logger.info(self._locationmap)
        return self._locationmap

def main():
    app = Beacon2Map()
    app.setWindowIcon(QIcon(QPixmap(config.icon['app'])))
    window = MainWindow(app)
    window.resize(config.window_width, config.window_height)
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()

# TODO Fix inversion when fast zooming out
# TODO File selection form
# TODO Marker type checkboxes
