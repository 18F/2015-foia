import argparse
import json
import os
import shutil
import sys

import requests
from foia_hub.settings.base import BASE_DIR


# TODO: Should this be a part of a generic utilities for data stuff?
# This is also used in the general contacts directory
DEFAULT_DATA_FOLDER = 'foia/usa-contacts/data'


def _get_data_folder():
    return BASE_DIR.rstrip('/foia_hub').rstrip('foia-') + DEFAULT_DATA_FOLDER


def setup_data_dir():
    '''
        Setup a data dir if it doesn't exist.
    '''
    # Make a data directory if it doesn't exist
    if not os.path.isdir("data"):
        os.mkdir("data")
        return True
    return False


def grab_and_save_data():
    '''
        Grabs contacts data from the USAGovAPI
    '''

    url = 'http://www.usa.gov/api/USAGovAPI/contacts.json/contacts'
    r = requests.get(url)

    data = r.json()['Contact']

    setup_data_dir()
    with open('data/all_usa_data.json', 'w') as outfile:
        json.dump(data, outfile)


def create_sample_file(sample_recs,
                        data_source='data/all_usa_data.json'):
    '''
        Example: create_sample_file([0, 100, 250, 400], 'data/all_data.json')
        Pulls indexed records from full datasets to create sample data.
    '''

    # Load file with all data
    try:
        data = json.load(open(data_source))
    except FileNotFoundError:
        grab_and_save_data()
        data = json.load(open(data_source))

    samples = []

    for n in sample_recs:
        samples.append(data[n])

    with open('data/sample_data.json', 'w') as outfile:
        json.dump(samples, outfile)



if __name__ == "__main__":

    '''
        This script serves two purposes -- pull down contacts from usa.gov create a sample file from the data pulled down.

        To pull down fresh data from for agency contact info from usa.gov:

            python usagov.py

            The result will be saved in 'data/'.

        To generate a sample file from the data, run the following:

            python usagov.py --create-sample
            or
            python usagov.py --create-sample 1 2 3 4 56 394

            In the first version, the default records will be used. In the second, the rec numbers that you specified will be used.
            If the usa.gov contacts file does not exist locally, a fresh pull will occur. If the file exists locally, then the script will used the existing file.

    '''

    parser = argparse.ArgumentParser(description='usagov.py scripts pulls contact records from usa.gov.')
    parser.add_argument('--create-sample',
                        dest='sample', nargs='*', type=int,
                        help='Generates a file of sample records Grab sample records based on position num. Pass a list of numbers to generate the file. Default will be generated if flag passed without values -- 10 100 200 300 400.',
                        )
    args = parser.parse_args()
    sample = args.sample

    # If flag was passed, but empty, create a default predictable list of recs.
    if (type(sample) is list) and (len(sample) is 0):
        sample = [10,100,200,300,400]

    if sample:
        create_sample_file(sample)
    else:
        grab_and_save_data()
