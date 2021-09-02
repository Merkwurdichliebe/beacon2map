#!/usr/bin/env python
 
'''
Load a YML configuration file based on context (development version or final
app version).
'''

import os
from types import SimpleNamespace
import yaml
from utility import logger, find_file_in_resources

logger = logger()

FILE_DEV = 'configmine.yml'
FILE_APP = 'config.yml'


def read_yml(filename):
    '''Return a YAML file as a dictionary'''
    try:
        with open(filename, encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data
    except Exception as e:
        raise RuntimeError(
            f'Missing or invalid configuration file\n({e})') from e

# Get the directory of this module
# config_dir = os.path.abspath(os.path.dirname(__file__))

# Use a local development config file if present
if os.path.isfile(find_file_in_resources(FILE_DEV)):
    file = FILE_DEV
else:
    file = FILE_APP

logger.info(f'Using config file: {FILE_DEV}')

# Get the YAML configuration file as a dictionary
config_dict = read_yml(find_file_in_resources(file))

# Get correct file path based on context (app frozen or not)
for k, v in config_dict['icon'].items():
    config_dict['icon'][k] = find_file_in_resources(v)

# Unpack the dictionary to a namespace
# to allow access through dot notation
config = SimpleNamespace(**config_dict)
