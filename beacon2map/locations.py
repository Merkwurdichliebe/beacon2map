import math
import logging
from dataclasses import dataclass

from json.encoder import JSONEncoder
from json.decoder import JSONDecoder


logger = logging.getLogger(__name__)


@dataclass
class Extents:
    min_x: int
    max_x: int
    min_y: int
    max_y: int
    min_z: int = 0
    max_z: int = 0


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


    def __init__(self, distance, bearing, depth, reference_depth=None):
        # Variables validated through properties
        self._distance = None
        self._bearing = None
        self._depth = None
        self._name = None
        self._category = None
        self._description = None

        # Regular instance variables
        self.reference_depth = reference_depth
        self.done = False

        # Initialize properties
        self.distance = distance
        self.bearing = bearing
        self.depth = depth

    # Utility methods

    @staticmethod
    def get_adjacent_side(hyp: int, opp: int) -> int:
        try:
            result = round(math.sqrt(hyp**2 - opp**2))
        except ValueError as e:
            raise ValueError(f'Invalid triangle values ({e}).')
        else:
            return result 

    @staticmethod
    def get_heading(bearing: int) -> int:
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
        # if value - self.reference_depth > self.distance:
        #     raise ValueError('Depth cannot be greater than distance')
        self._depth = value

    @property
    def name(self):
        return self._name or 'Untitled'

    @name.setter
    def name(self, value):
        if value is not None:
            self._name = str(value)

    @property
    def category(self):
        return self._category or 'default'

    @category.setter
    def category(self, value):
        self._category = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        if value == '':
            value = None
        self._description = value

    # Read-only properties

    @property
    def surface_distance(self):
        return self.get_adjacent_side(
            self.distance, abs(self.depth - self.reference_depth))

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
        rep = f'{__name__}.Location object: {self.name}'
        rep += f' ({self.distance} {self.heading}° {self.depth}m)'
        rep += ' [Description]' if self.description else ''
        rep += ' Done' if self.done else ''
        return rep


class LocationJSONEncoder(JSONEncoder):
    def default(self, o):
        if not isinstance(o, Location):
            return super().default(o)
        return {
            'name': o.name,
            'description': o.description,
            'category': o.category,
            'distance': o.distance,
            'bearing': o.bearing,
            'depth': o.depth,
            'done': o.done
        }


# class LocationJSONDecoder(JSONDecoder):
#     def __init__(self):
#         super().__init__(object_hook=self.dict_to_obj)

#     def dict_to_obj(self, d):
#         args = {key: value for key, value in d.items()}
#         return Location(**args)

class LocationMap:
    '''
    LocationMap hold a list of Location objects
    and calculates their extents in 3 dimensions.
    '''

    def __init__(self, locations: list[Location] = None, reference_depth: int = 0):
        assert isinstance(locations, list)
        for item in locations:
            assert isinstance(item, Location)

        self.locations = locations
        self.reference_depth = reference_depth
        for location in locations:
            location.reference_depth = self.reference_depth

        logger.debug('Location Map init done.')

    def delete(self, location: Location) -> None:
        try:
            self.locations.remove(location)
            logger.debug('Location deleted : %s.', location)
        except ValueError as e:
            msg = f'Can\'t delete from LocationMap , no such location: {location}'
            raise RuntimeError(msg) from e

    @property
    def reference_depth(self):
        return self._reference_depth or 0
    
    @reference_depth.setter
    def reference_depth(self, value: int):
        self._reference_depth = value

    @property
    def extents(self) -> Extents:
        if not self.locations:
            return Extents(0, 0, 0, 0)
        else:
            return Extents(
                min([loc.x for loc in self.locations]),
                max([loc.x for loc in self.locations]),
                min([loc.y for loc in self.locations]),
                max([loc.y for loc in self.locations]),
                min([loc.depth for loc in self.locations]),
                max([loc.depth for loc in self.locations])
            )

    @property
    def size(self) -> int:
        return len(self.locations)

    def __repr__(self):
        rep = f'{__name__}.LocationMap object ({self.size} locations) '
        rep += f'Extents: {self.extents}'
        return rep
