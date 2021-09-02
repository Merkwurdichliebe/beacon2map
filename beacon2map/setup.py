from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options_exe = {}

build_options_app = {
    'iconfile': 'resources/icon-app.icns',
    'bundle_name': 'beacon2map',
    'include_resources': [
        ('configmine.yml', 'configmine.yml'),
        ('config.yml', 'config.yml'),
        ('icons/icon-app.png', 'icons/icon-app.png'),
        ('icons/reload-128.png', 'icons/reload-128.png'),
        ('icons/save-128.png', 'icons/save-128.png'),
        ('icons/zoom-128.png', 'icons/zoom-128.png'),
        ('icons/grid-128.png', 'icons/grid-128.png'),
        ('icons/add-128.png', 'icons/add-128.png'),
        ('data/locations.json', 'data/locations.json')
        ]
    }

build_options_dmg = {
    'volume_label': 'beacon2map'
}

import sys
base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable(
        'beacon2map.py',
        base=base, 
        target_name='beacon2map')
]

setup(name='beacon2map',
      version='1.0',
      description='',
      options={
          'build_exe': build_options_exe,
          'bdist_mac': build_options_app,
          'bdist_dmg': build_options_dmg
          },
      executables=executables)
