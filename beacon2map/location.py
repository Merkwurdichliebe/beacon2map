#!/usr/bin/env python

import math
import logging
from dataclasses import dataclass
from json.encoder import JSONEncoder

logger = logging.getLogger(__name__)


#
# Extents utility data class
#


@dataclass
class Extents:
    min_x: int
    max_x: int
    min_y: int
    max_y: int
    min_z: int = 0
    max_z: int = 0


#
# SubVector Class
#


class SubVector:
    '''
    SubVector defines an abstract position in 3d space using a vector
    length, z-value and angle. It can then return x and y values for the
    vector projected vertically unto these axes. It's like looking at the
    origin from somewhere, noting the distance to the origin and your
    position in z, and getting the x/y position at z=0 (which is basically
    all this app does).
    '''
    def __init__(self, length, z, angle, z_offset=0):
        self.length = None
        self.z = None
        self.xy_projection = None
        self.z_offset = z_offset

        self.set_length_and_z(length, z)

        self._angle = None
        self.angle = angle

    def set_length_and_z(self, length: int, z: int) -> None:
        if self.is_valid_vector(length, abs(self.z_offset - z)):
            self.length = length
            self.z = z
            self.xy_projection = self.get_adjacent_side(
                length, self.z_offset - z)
        else:
            raise ValueError(
                'Invalid vector '
                f'(length={length}, z={z}, z_offset={self.z_offset}).')

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        if 0 <= value <= 360:
            self._angle = value
        else:
            raise ValueError(
                f'Invalid vector angle {value}, should be between 0 and 360.')

    @property
    def x(self):
        sin = math.sin(math.radians((self.angle - 180) % 360))
        return int(sin * self.xy_projection)

    @property
    def y(self):
        cos = math.cos(math.radians((self.angle - 180) % 360))
        return int(cos * -self.xy_projection)  # Invert y for Qt

    # Utility functions

    @staticmethod
    def is_valid_vector(length: int, z: int) -> bool:
        return abs(z) <= length

    @staticmethod
    def get_adjacent_side(hypotenuse: int, side: int) -> int:
        if side > hypotenuse:
            raise ValueError('Invalid triangle')
        else:
            return round(math.sqrt(hypotenuse**2 - side**2))

    def __repr__(self):
        rep = f'{__name__}.Vector object:'
        rep += f' ({self.length}, {self.z}, {self.angle},'
        rep += f' x={self.x} y={self.y})'
        return rep


#
# Location Class
#


class Location(SubVector):
    '''
    Location renames some of the methods and properties of SubVector and adds
    game-related fields such as name, category, description and done status.
    '''
    def __init__(self, distance: int, depth: int, bearing: int, reference_depth: int = 0):
        super().__init__(distance, depth, bearing, reference_depth)
        self._name = None
        self._category = None
        self._description = None
        self._done = None

        self.reference_depth = reference_depth

    def set_distance_and_depth(self, distance: int, depth: int) -> None:
        try:
            super().set_length_and_z(distance, depth)
        except ValueError as e:
            raise ValueError from e

    @property
    def distance(self):
        return self.length

    @property
    def depth(self):
        return self.z

    @property
    def bearing(self):
        return self.angle

    @bearing.setter
    def bearing(self, value):
        self.angle = value

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
        self._category = str(value)

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        self._description = value

    @property
    def done(self):
        return self._done or False

    @done.setter
    def done(self, value):
        self._done = bool(value)

    def __repr__(self):
        rep = f'{__name__}.Location object: {self.name}'
        rep += f' ({self.distance} {self.depth}m {self.bearing}°)'
        rep += ' [Description]' if self.description else ''
        rep += ' Done' if self.done else ''
        return rep


#
# JSONEncoder for Location Class
#


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


#
# LocationMap Class
#


class LocationMap:
    '''
    LocationMap is responsible for keeping a list of Location object, adding
    and deleting them, and calculating their extents (minimum and maximum) in
    3d space.
    '''
    def __init__(self, reference_depth: int = 0):
        self.reference_depth = reference_depth
        self.locations = []
        logger.debug(
            f'Location Map created with reference depth {self.reference_depth}.')

    def add_location(self, distance: int, depth: int, bearing: int) -> Location:
        try:
            location = Location(distance, depth, bearing, self.reference_depth)
        except ValueError as e:
            raise ValueError(f'Error adding location to map. {e}') from e
        self.locations.append(location)
        return location

    def delete_location(self, location: Location) -> None:
        if location not in self.locations:
            raise ValueError('Trying to delete non-existent location.')
        else:
            self.locations.remove(location)

    @property
    def size(self) -> int:
        return len(self.locations)

    @property
    def extents(self) -> Extents:
        if self.size == 0:
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

    def __repr__(self):
        rep = f'{__name__}.LocationMap object ({self.size} locations) '
        rep += f'Extents: {self.extents}'
        return rep
