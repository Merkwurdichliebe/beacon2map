import os
import yaml

def read_config_yml(filename):
    try:
        with open(filename, encoding='utf-8') as file:
            data = yaml.safe_load(file)
            return data
    except Exception as e:
        msg = f'Missing or invalid configuration file\n({e})'
        raise RuntimeError(msg) from e

if os.path.isfile(os.getcwd() + '/configmine.py'):
    cfg = read_config_yml('configmine.yml')
else:
    cfg = read_config_yml('config.yml')