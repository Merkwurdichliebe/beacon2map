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
from beacon2map.locations import Location, LocationMap, LocationJSONEncoder


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

        self.locationmap = None

        # Make Qt search through the font list early
        self.setFont(QFont(cfg.font_family))

        # Load the location data from file
        # and create the locationmap object
        json_dict = self.load(cfg.filename)
        locs = self.create_locations_from_json(json_dict)
        self.locationmap = LocationMap(locs)

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
            assert isinstance(data, list)
            logger.info(f'\'{file}\' file load successful.')
            return data

    @staticmethod
    def create_locations_from_json(data: dict) -> list[Location]:
        '''Instantiate Location object from the JSON data
        and create a LocationMap object.
        '''
        locations = []
        for item in data:
            try:
                loc = Location(
                    item['distance'], item['bearing'], item['depth'])
                loc.name = item['name']
                loc.category = item['category']
                loc.description = item['description']
                loc.done = item['done']
            except (ValueError, KeyError) as e:
                msg = f'\nError parsing location: {item}: {e}.'
                raise RuntimeError(msg) from e
            else:
                if loc not in locations:
                    locations.append(loc)
        return locations

    @staticmethod
    def create_locationmap(locations: list[Location]) -> LocationMap:
        locationmap = LocationMap(locations)
        logger.debug(f'Successfully created {locationmap.size} locations.')
        return locationmap

    def save(self) -> None:
        filename = 'locations.json'
        logger.info('Saving data to %s', filename)
        try:
            with open(filename, 'w') as write_file:
                json.dump(
                    self.locationmap.locations,
                    write_file,
                    indent=4,
                    # FIXME ensure_ascii=False,
                    cls=LocationJSONEncoder
                )
        except IOError as error:
            logger.error('Save failed: %s.', error)
        else:
            logger.info('Save successful.')

    def add_location(self) -> None:
        loc = Location(50, 50, 50)
        loc.name = 'Test'
        self.locationmap.locations.append(loc)
        logger.debug(f'Added Location : {loc}')
        return loc

    def delete_location(self, location: Location) -> None:
        self.locationmap.delete(location)
        msg = f'Deleted Location: {location} — '
        msg += f'Map size is now {self.locationmap.size} elements.'
        logger.debug(msg)


def main():
    app = Beacon2Map()
    app.setWindowIcon(QIcon(QPixmap(cfg.icon['app'])))
    window = MainWindow(app)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

# TODO GridPoint should be added without Location ! only x y 
# TODO implement GraphicsScene focusitem
# TODO Fix save overwriting file if error
# TODO keep backup location data
# TODO Ask to save if data modified
# TODO Constrain editing gridpoints to valid values in inspector
# TODO Add new point
# TODO Fix inversion when fast zooming out
# TODO File selection form
# TODO Reciprocal display on bearing in inspector
# TODO debug mode
