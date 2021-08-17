# General utility module

import os
import platform
import logging
from dataclasses import dataclass


def get_path(filename):
    """Return the full path for the passed filename. This works cross-platform
    and uses AppKit to refer to the path when used on macOS.
    This uses code suggested on this pyinstaller issues page:
    https://github.com/pyinstaller/pyinstaller/issues/5109#issuecomment-683313824"""
    name = os.path.splitext(filename)[0]
    ext = os.path.splitext(filename)[1]
    if platform.system() == "Darwin":
        from AppKit import NSBundle
        file = NSBundle.mainBundle().pathForResource_ofType_(name, ext)
        return file or os.path.realpath(filename)
    else:
        return os.path.realpath(filename)


def logger():
    '''Default logger for main script.'''
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


def logit(function):
    '''Decorator that prints function calls to console.'''
    def wrapper(*args, **kwargs):
        a = f'-- {args}' if args else ''
        k = f': {kwargs}' if kwargs else ''
        print(f'  LOGIT  {function.__name__} {a} {k}')
        return function(*args, **kwargs)
    return wrapper


def scale_value(value, value_min, value_max, dest_min, dest_max, inverted=False):
    '''Scale value between min & max values to destination min/max equivalent.'''
    normalized = (value - value_min) / value_max
    if inverted:
        normalized = 1 - normalized
    scaled = normalized * (dest_max - dest_min) + dest_min
    return scaled


@dataclass
class Extents:
    min_x: int
    max_x: int
    min_y: int
    max_y: int
    min_z: int = 0
    max_z: int = 0