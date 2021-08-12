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
import yaml

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QIcon

from beacon2map.mainwindow import MainWindow
from beacon2map.locations import LocationMap

# Use local config file if present
if os.path.isfile('configmine.py'):
    import configmine as cfg
else:
    import config as cfg

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Beacon2Map(QApplication):
    '''Main application/controller object for beacon2map.'''
    def __init__(self):
        super().__init__()

        self._locationmap = None
        self.has_valid_map = False
        self.cfg = None

        self.cfg = self.read_config_yml()

    @staticmethod
    def read_config_yml():
        if os.path.isfile(os.getcwd() + '/configmine.py'):
            filename = 'configmine.yml'
        else:
            filename = 'config.yml'

        try:
            with open(filename, encoding='utf-8') as file:
                data = yaml.safe_load(file)
                return data
        except Exception as e:
            msg = f'Missing or invalid configuration file\n({e})'
            raise RuntimeError(msg) from e


    @property
    def locationmap(self):
        '''Create a LocationMap object from CSV file.
        This property reloads the file whenever its requested,
        to allow for data reload.
        '''
        try:
            self._locationmap = LocationMap(cfg.filename)

        except RuntimeError as e:
            msg = f'\nApp cannot create Location Map {e}'
            raise RuntimeError(msg) from e
        else:
            logger.info('Beacon2Map: Locations loaded from %s', cfg.filename)
            logger.info(self._locationmap)
            self.has_valid_map = True
            return self._locationmap

def main():
    app = Beacon2Map()
    app.setWindowIcon(QIcon(QPixmap(cfg.icon['app'])))
    window = MainWindow(app)
    if app.has_valid_map:
        window.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    main()

# TODO Fix inversion when fast zooming out
# TODO File selection form
# TODO Marker type checkboxes
