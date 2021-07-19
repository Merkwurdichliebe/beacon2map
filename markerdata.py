#!/usr/bin/env python

"""
This module is a helper class for beacon2map.py

It reads a CSV file of beacon markers and calculates x and y positions
from bearing and distance data.
"""

__author__ = "Tal Zana"
__copyright__ = "Copyright 2021"
__license__ = "GPL"
__version__ = "1.0"

import pandas as pd
import math

REF_DEPTH = 100             # Depth of the reference beacon


class MarkerData():
    def __init__(self, filename):
        # Read CSV file
        # Distance,Bearing,Depth,Name,Marker,Done,Description
        # e.g.:
        # 988,355,458,Caves,interest,,"Cave network detected below"
        # Lowercase 'x' is used to flag a marker as 'Done'
        df = pd.read_csv(filename, na_filter=False)

        # Calculate a horizontal distance to the reference point
        delta = df['Distance']**2 - (df['Depth']-REF_DEPTH)**2
        df['h'] = round(delta.apply(math.sqrt)).astype(int)

        # Reverse the bearing (CSV holds the heading to the reference)
        df['dir'] = (df['Bearing'] - 180) % 360

        # Calculate the x coordinates from the distance and heading
        df['x'] = (df['dir'].apply(
            math.radians).apply(math.sin) * df['h']).astype(int)

        # Same for y, which is inverted in order to be read correctly
        # by the Qt coordinate system
        df['y'] = (df['dir'].apply(
            math.radians).apply(math.cos) * -1 * df['h']).astype(int)

        # Convert everything to a single list of markers in tuple form
        x = df['x'].tolist()
        y = df['y'].tolist()
        marker = df['Marker'].tolist()
        label = df['Name'].tolist()
        depth = df['Depth'].tolist()
        done = df['Done'].tolist()
        desc = df['Description'].tolist()
        self._markers = zip(x, y, marker, label, depth, done, desc)

        self._extents_x = (df['x'].min(), df['x'].max())
        self._extents_y = (df['y'].min(), df['y'].max())

    def get_markers(self):
        return self._markers

    def get_extents(self):
        return (self._extents_x, self._extents_y)
