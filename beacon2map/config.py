#!/usr/bin/env python
 
'''
Load a YML configuration file based on context (development version or final
app version).
'''

import os
from types import SimpleNamespace
import yaml


FILE_DEV = 'configmine.yml'
FILE_APP = 'config.yml'


def read_yml(filename):
    '''Return a YAML file as a dictionary'''
    try:
        with open(filename, encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data
    except Exception as e:
        msg = f'Missing or invalid configuration file\n({e})'
        raise RuntimeError(msg) from e


# Get the directory of this module
config_dir = os.path.abspath(os.path.dirname(__file__))

# Use a local development config file if present
if os.path.isfile(os.path.join(config_dir, ('configmine.yml'))):
    file = FILE_DEV
else:
    file = FILE_APP

# Get the YAML configuration file as a dictionary
config_dict = read_yml(os.path.join(config_dir, file))

# Unpack the dictionary to a namespace
# to allow access through dot notation
config = SimpleNamespace(**config_dict)
