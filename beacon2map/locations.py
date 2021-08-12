import os
import math
import pandas as pd
if os.path.isfile('configmine.py'):
    import configmine as cfg
else:
    import config as cfg


class LocationMap:
    '''
    LocationMap holds Location objects read from a CSV file
    and calculates their maximum x and y extents.

    Args:
        filename (str): full path to CSV file
    Returns:
        LocationMap object
    Raises:
        FileNotFoundError: if filename is not found
        KeyError: if column name doesn't exist in CSV file
        ValueError: if CSV contains invalid data (e.g. strs intead of ints)
    '''
    def __init__(self, filename: str):

        # Load the dataframe from CSV
        self._data = self.read_csv(filename)

        # If data is valid, create the list of Location objects
        if self._data is not None:
            try:
                self._locations = self.get_locations()
            except (ValueError, KeyError) as error:
                raise RuntimeError(
                    f'\nCSV file contains invalid data {error}') from error
        else:
            self._locations = None

        # If locations have been added, calculate their total x/y extents
        if self.locations:
            self.extents = self.get_extents()
        else:
            self.extents = ((0,0), (0,0))

    @staticmethod
    def read_csv(filename):
        '''Load a CSV file and return a Pandas Dataframe.'''
        try:
            df = pd.read_csv(filename, na_filter=False)
        except FileNotFoundError as e:
            msg = f'\nCSV file not found: {filename}'
            raise RuntimeError(msg) from e
        else:
            return df

    def get_locations(self):
        '''Iterate through pandas Dataframe and build a list
        of Location objects.'''
        locs = []
        for index, row in self._data.iterrows():
            try:
                # Use exception to validate integers only here
                loc = Location(
                    int(row['distance']),
                    int(row['bearing']),
                    int(row['depth']))

                # Name can be anything
                loc.name = row['name']

                # Pandas indices start at 0, we start at 1
                loc.id = index + 1

                loc.category = row['category']
                if row['description']:
                    loc.description = row['description']

                # Consider any non-whitespace character as a 'done' flag
                done = ''.join(row['done'].split())
                if done:
                    loc.done = True

            except ValueError as error:
                msg = f'\nError reading row {index} {error}\n'
                raise ValueError(msg) from error
            except KeyError as error:
                msg = f'\nError reading column name {error} from CSV file.'
                raise KeyError(msg) from error
            else:
                locs.append(loc)

        return locs

    def get_extents(self):
        min_x = min([loc.x for loc in self.locations])
        max_x = max([loc.x for loc in self.locations])
        min_y = min([loc.y for loc in self.locations])
        max_y = max([loc.y for loc in self.locations])
        return ((min_x, min_y), (max_x, max_y))

    @property
    def locations(self):
        return self._locations or []

    @property
    def min_x(self):
        return self.extents[0][0]

    @property
    def min_y(self):
        return self.extents[0][1]

    @property
    def max_x(self):
        return self.extents[1][0]

    @property
    def max_y(self):
        return self.extents[0][1]

    @property
    def depth_extents(self):
        min_depth = min([loc.depth for loc in self.locations])
        max_depth = max([loc.depth for loc in self.locations])
        return min_depth, max_depth

    @property
    def elements(self):
        return len(self.locations)

    def __repr__(self):
        rep = f'{__name__}.LocationMap object ({self.elements} locations) '
        rep += f'Extents: {self.extents}'
        return rep


class Location:
    '''
    A map location measured in distance, bearing and depth
    relative to a known reference point.

    Args:
        distance (int): distance to reference
        bearing (int): bearing (in degrees) to deference
        depth (int): depth measured from
    Returns:
        Location object
    Raises:
        ValueError for invalid values
    '''

    # TODO Default depth of reference beacon should be set elsewhere
    reference_depth = 100

    def __init__(self, distance, bearing, depth):
        self.distance = distance
        self.bearing = bearing
        self.depth = depth
        self.done = False
        self.id = None
        self.description = None

        self._name = None
        self._category = None

    def set_reference_depth(self, depth):
        self.reference_depth = depth

    # Utility methods

    @staticmethod
    def get_adjacent_side(hyp, opp):
        return round(math.sqrt(hyp**2 - opp**2))

    @staticmethod
    def get_heading(bearing):
        return (bearing - 180) % 360

    # Read/Write properties

    @property
    def distance(self):
        return self._distance

    @distance.setter
    def distance(self, value):
        if not value >= 0:
            raise ValueError('Distance cannot be a negative number')
        self._distance = value

    @property
    def bearing(self):
        return self._bearing

    @bearing.setter
    def bearing(self, value):
        if not 0 <= value <= 360:
            raise ValueError('Bearing must be between 0 and 360')
        self._bearing = value

    @property
    def depth(self):
        return self._depth

    @depth.setter
    def depth(self, value):
        if not value >= 0:
            raise ValueError('Depth cannot be a negative number')
        elif value - self.reference_depth > self.distance:
            raise ValueError('Depth cannot be greater than distance')
        self._depth = value

    @property
    def name(self):
        return self._name or 'Untitled'

    @name.setter
    def name(self, value):
        self._name = str(value)

    @property
    def category(self):
        return self._category or 'default'

    @category.setter
    def category(self, value):
        self._category = value

    # Read-only properties

    @property
    def surface_distance(self):
        return self.get_adjacent_side(
            self.distance, self.depth - self.reference_depth)

    @property
    def heading(self):
        return self.get_heading(self.bearing)

    @property
    def x(self):
        sin = math.sin(math.radians(self.heading))
        return int(sin * self.surface_distance)

    @property
    def y(self):
        cos = math.cos(math.radians(self.heading))
        return int(cos * -self.surface_distance) # Invert y axis for Qt

    def __repr__(self):
        rep = f'{__name__}.Location object: {self.name} '
        rep += f'({self.distance} {self.heading}° {self.depth}m)'
        return rep
