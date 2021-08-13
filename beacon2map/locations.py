import math
import logging
from json.encoder import JSONEncoder
from json.decoder import JSONDecoder

from collections import namedtuple

Extents = namedtuple(
    'Extents', ['min_x', 'max_x', 'min_y', 'max_y', 'min_z', 'max_z'])

logger = logging.getLogger(__name__)


class LocationMap:
    '''
    LocationMap hold a list of Location objects
    and calculates their extents in 3 dimensions.
    '''
    def __init__(self, locations=None):
        assert isinstance(locations, list)
        for item in locations:
            assert isinstance(item, Location)

        self.locations = locations
        logger.debug('Location Map init done.')

    def delete(self, location):
        try:
            self.locations.remove(location)
            logger.debug('Location deleted: %s.', location)
        except ValueError as e:
            msg = f'Can\'t delete from LocationMap , no such location: {location}'
            raise RuntimeError(msg) from e

    @property
    def extents(self):
        if not self.locations:
            return None
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
    def size(self):
        return len(self.locations)

    def __repr__(self):
        rep = f'{__name__}.LocationMap object ({self.size} locations) '
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
        self.name = None
        self.category = None
        self.done = False
        self.id = None
        self.description = None

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