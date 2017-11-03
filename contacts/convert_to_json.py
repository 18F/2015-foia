#!/usr/bin/env python
import json
import logging
import os.path
import yaml
from glob import glob

logger = logging.getLogger('convert_to_json')

def convert_to_json():
    for filename in glob("data" + os.sep + "*.yaml"):
        logger.debug('found yaml file filename=%s' % filename)
        with open(filename) as f:
            yaml_data = yaml.load(f.read())

        agency, _ = os.path.splitext(os.path.basename(filename))
        logger.info('converting to json agency=%s' % agency)
        with open(os.sep.join(['data', '%s.json' % agency]), 'w') as f:
            f.write(json.dumps(yaml_data, sort_keys=True, indent=2))

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    convert_to_json()
