#!/usr/bin/env python
import os
from glob import glob

import yaml

import scraper


def layer_manual_data(agency_abbr):
    filename = scraper.agency_yaml_filename('data', agency_abbr)
    with open(filename, 'r') as f:
        print(filename)
        agency_data = yaml.load(f)
        data = scraper.apply_manual_data(agency_abbr, agency_data)
        scraper.save_agency_data(agency_abbr, data)

if __name__ == "__main__":
    for agency_abbr in scraper.AGENCIES:
        layer_manual_data(agency_abbr)
