#!/usr/bin/env python

"""
beacon2map creates a visual map based on readings of distance, depth and
bearing relative to a central reference beacon.

This app was designed as an exploration aid for the video game Subnautica.

Requirements: Qt6 for Python (PySide6)

-- Application structure

SubVector defines an abstract position in 3d space. Location subclasses
SubVector and adds several game-related properties. LocationMap is responsaible
for keeping track of Location objects.

MainWindow subclasses QMainWindow, builds the GUI and handles user interaction.
MainWidget serves as the central widget and holds the MapScene object. MapScene
subclasses QGraphicsScene and handles the display of GridPoint objects. MapView
subclasses QGraphicsView and mainly handles zooming and dragging.

GridPoint subclasses QGraphicsObject and displays point information based on
the Location objects.

ToolbarFilterWidget holds the category filtering interface in the toolbar.
GridpointInspector subclasses QGroupBox and serves as a floating inspector for
displaying and editing Gridpoint objects.

Beacon2Map (in this file) is responsible for loading and saving the location
data, and for configuring the logger.

"""

__author__ = "Tal Zana"
__copyright__ = "Copyright 2021"
__license__ = "GPL"
__version__ = "1.0"


import sys
import json

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QPixmap, QIcon

from config import config as cfg
from mainwindow import MainWindow
from location import Location, LocationMap, LocationJSONEncoder
from utility import logger, logit

#
# Set up logging
#


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
        self.settings = cfg.json_defaults

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
        logger.debug(
            f'Added {map.size} locations from saved data.')
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
        logger.debug(
            f'Deleted Location: {location} — '
            f'Map size is now {self.map.size} elements.')


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
# TODO debug mode
# TODO set tab order
# TODO move radio buttons out of filter widget
# TODO adapt icons to dark mode https://github.com/cbrnr/mnelab/issues/151
# TODO redraw grid if location extents change
# TODO animate view to new location position if offscreen
# TODO fix filter calls on checkbox init
# TODO Set Gridpoint zValue based on depth
# FIXME Inspector prevents selection below on startup
# TODO recalculate grid extents on GridPoint change
