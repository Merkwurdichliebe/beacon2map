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
import json
import logging

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QIcon

from beacon2map.config import config as cfg
from beacon2map.mainwindow import MainWindow
from beacon2map.locations import Location, LocationMap, LocationJSONEncoder

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Beacon2Map(QApplication):
    '''Main application/controller object for beacon2map.'''
    def __init__(self):
        super().__init__()

        self.main_window = None
        self.locationmap = None
        self.has_valid_map = False

        self.load()

    def validate_map(self):
        for i, location in enumerate(self._locationmap.locations):
            if location.category not in cfg.categories:
                msg = f'\nInvalid category at line {i+1}: {location.category}'
                raise RuntimeError(msg)

    def delete_location(self, location):
        self._locationmap.delete(location)
        logger.info('Deleted Location: %s', location)
        self.main_window.populate_scene()

    def load(self):
        filename = 'locations.json'
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
        except IOError as error:
            logger.info('Load failed: %s', error)
        else:
            logger.info('Load successful')
            self.create_locations_from_json(data)

    def create_locations_from_json(self, data):
        locations = []
        try:
            for item in data:
                loc = Location(item['distance'], item['bearing'], item['depth'])
                loc.name = item['name']
                loc.category = item['category']
                loc.description = item['description']
                loc.done = item['done']
                if loc not in locations:
                    locations.append(loc)
            self.locationmap = LocationMap(locations)
        except ValueError as e:
            msg = 'Error reading saved locations.'
            raise RuntimeError(msg) from e
        else:
            self.has_valid_map = True
            msg = f'Successfully created {self.locationmap.elements} locations.'
            logger.info(msg)

    def save(self):
        filename = 'locations.json'
        logger.info('Saving data to %s', filename)
        try:
            with open(filename, 'w') as write_file:
                json.dump(
                    self._locationmap.locations,
                    write_file,
                    indent=4,
                    # FIXME ensure_ascii=False,
                    cls=LocationJSONEncoder
                )
        except IOError as error:
            logger.info('Save failed: %s', error)
        else:
            logger.info('Save successful')


def main():
    app = Beacon2Map()
    if app.has_valid_map:
        app.setWindowIcon(QIcon(QPixmap(cfg.icon['app'])))
        window = MainWindow(app) # don't forget to move sys.exit back 
        window.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    main()

# TODO Fix inversion when fast zooming out
# TODO File selection form
# TODO Marker type checkboxes
