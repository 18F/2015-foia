import json
import sys
import os

import requests
from foia_hub.settings.base import BASE_DIR


# TODO: Should this be a part of a generic utilities for data stuff?
# This is also used in the general contacts directory
DEFAULT_DATA_FOLDER = 'foia/usa-contacts/data'


def _get_data_folder():
    return BASE_DIR.rstrip('/foia_hub').rstrip('foia-') + DEFAULT_DATA_FOLDER


def grab_and_save_data():
    '''
        Grabs contacts data from the USAGovAPI
    '''

    url = 'http://www.usa.gov/api/USAGovAPI/contacts.json/contacts'
    r = requests.get(url)

    data = r.json()['Contact']

    with open('all_data.json', 'w') as outfile:
        json.dump(data, outfile)


def create_sample_file(sample_numbers, data='data/all_data.json'):
    '''
        Example: create_sample_file([0, 100, 250, 400], 'data/all_data.json')
        Pulls indexed records from full datasets to create sample data.
    '''

    samples = []
    #TODO: Add data file load.
    for n in sample_numbers:
        samples.append(data[n])

    with open('data/sample_data.json', 'w') as outfile:
        json.dump(samples, outfile)


# Just like the the note at the top, this function is similar to stuff
# happening in the processing yaml file in contacts.
def load_saved_data(data_source):
    folder = _get_data_folder()
    data_file = os.path.join(folder, data_source)
    print(data_file)
    data = json.load(open(data_file))
    print(data)
    return data


def trim_down_contact_info(data):
    ''' Function to trim done the info to the components that we need.'''
    pass


def _get_key_or_none(rec, primary, secondary=None):
    '''
        This was written to pull out all urls from the record.
        To use:

        urls = []
        for rec in urls:
            urls.append((
                    _get_key_or_none(rec, 'Contact_Url', 'Url'),
                    _get_key_or_none(rec, 'Web_Url', 'Url'),
                    _get_key_or_none(rec, 'In_Person_Url', 'Url'),
                    _get_key_or_none(rec, 'Source_Url', 'Url'),
                    ))
        pprint(urls)
    '''

    try:
        values = []
        if isinstance(rec[primary], list):
            for item in rec[primary]:
                values.append(item[secondary])
        else:
            try:
                values.append(rec[primary][secondary])
            except TypeError:
                values.append(rec[primary])
        return values
    except KeyError:
        return None


def get_all_urls(data):
    urls = []
    for rec in data:
        urls.append((
            _get_key_or_none(rec, 'Contact_Url', 'Url'),
            _get_key_or_none(rec, 'Web_Url', 'Url'),
            _get_key_or_none(rec, 'In_Person_Url', 'Url'),
            _get_key_or_none(rec, 'Source_Url', 'Url'),
        ))
    #for i in urls:
    #    pprint.pprint(i)
    #    print('    ')
    return urls


if __name__ == "__main__":
    data_file = sys.argv[1]
    data = load_saved_data(data_file)
    urls = get_all_urls(data)
    print(urls)
