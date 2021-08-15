#!/usr/bin/env python

"""
beacon2map creates a visual map based on readings of
distance, depth and bearing relative to a central reference beacon.

This app was designed as an exploration aid for the video game Subnautica.

Requirements: Qt6 for Python (PySide6)
"""

__author__ = "Tal Zana"
__copyright__ = "Copyright 2021"
__license__ = "GPL"
__version__ = "1.0"

import sys
import json
import logging

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QPixmap, QIcon

from beacon2map.config import config as cfg
from beacon2map.mainwindow import MainWindow
from beacon2map.location import Location, LocationMap, LocationJSONEncoder


#
# Set up logging
#


def logger():
    # Create the logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # level for the main script

    # Remove PySide6 (or other) handlers
    for h in logger.handlers:
        logger.removeHandler(h)

    # Create handlers
    ch = logging.StreamHandler()
    fh = logging.FileHandler('log.log', mode='w')

    # Set level thresholds for each output
    ch.setLevel(logging.DEBUG)
    fh.setLevel(logging.DEBUG)

    # Create formatters
    ch.setFormatter(logging.Formatter(
        '[ %(levelname)s ] %(name)s : %(message)s'))
    fh.setFormatter(logging.Formatter(
        '%(asctime)s [ %(levelname)s ] %(name)s : %(message)s'))

    # Add handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger


logger = logger()


#
# Main application object
#


class Beacon2Map(QApplication):
    '''Main application/controller object for beacon2map,
    responsible for loading and saving the location data.'''
    def __init__(self):
        super().__init__()

        self.map = None
        self.settings = self.default_settings()

        # Make Qt search through the font list early
        self.setFont(QFont(cfg.font_family))

        # Load the application data from file
        # and create the locationmap object
        saved_json = self.load(cfg.filename)
        self.settings = saved_json['settings']
        self.map = self.build_location_map(
            saved_json['locations'], self.settings['reference_depth'])

        self.data_has_changed = False

    @staticmethod
    def load(file: str) -> dict:
        '''Load the JSON location file.'''
        try:
            with open(file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f'Locations file load failed (\'{file}\'): {e}')
            raise RuntimeError(f'File I/O Error : {e}') from e
        except FileNotFoundError as e:
            logger.debug(f'Locations file not found (\'{file}\'): {e}')
            return []
        else:
            assert isinstance(data, dict)
            logger.info(f'\'{file}\' file load successful.')
            return data

    def build_location_map(self, data: dict, ref_dept: int) -> LocationMap:
        map = LocationMap(ref_dept)
        for item in data:
            loc = map.add_location(
                item['distance'], item['depth'], item['bearing'])
            loc.name = item['name']
            loc.category = item['category']
            loc.description = item['description']
            loc.done = item['done']
        msg = f'Added {map.size} locations from saved data.'
        logger.debug(msg)
        return map

    def save(self) -> None:
        data = {
            'settings': self.settings,
            'locations': self.map.locations
        }
        logger.info('Saving data to %s', cfg.filename)
        try:
            with open(cfg.filename, 'w') as write_file:
                json.dump(
                    data,
                    write_file,
                    indent=4,
                    # FIXME ensure_ascii=False,
                    cls=LocationJSONEncoder
                )
        except IOError as error:
            logger.error('Save failed: %s.', error)
        else:
            self.data_has_changed = False
            logger.info('Save successful.')

    def add_location(self) -> None:
        loc = self.map.add_location(0, self.map.reference_depth, 0)
        self.data_has_changed = True
        logger.debug(f'Added Location : {loc}')
        return loc

    def delete_location(self, location: Location) -> None:
        self.map.delete_location(location)
        self.data_has_changed = True
        msg = f'Deleted Location: {location} — '
        msg += f'Map size is now {self.map.size} elements.'
        logger.debug(msg)

    def default_settings(self) -> dict:
        return {'reference_depth': 0}


def main():
    app = Beacon2Map()
    app.setWindowIcon(QIcon(QPixmap(cfg.icon['app'])))
    window = MainWindow(app)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

# Create json file if it doesn't exist
# TODO GridPoint should be added without Location ! only x y
# TODO implement GraphicsScene focusitem
# TODO Fix save overwriting file if error
# TODO keep backup location data
# TODO Fix inversion when fast zooming out
# TODO File selection form
# TODO Reciprocal display on bearing in inspector
# TODO debug mode
# TODO set tab order
# TODO set scene reference depth