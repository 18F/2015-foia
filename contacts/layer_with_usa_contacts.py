import os
import re
import yaml

from glob import glob
from requests_cache.core import CachedSession

"""
This script updates the yaml files with usa_id, description, and acronyms.
"""


USA_CONTACTS_API = 'http://www.usa.gov/api/USAGovAPI/contacts.json/contacts'
ACRONYM = re.compile('\((.*?)\)')

# Subsitutions and replacements for name, must be in this order
REPLACEMENTS = [
    ("Purchase from People Who Are Blind or Severely Disabled",
        "U.S. AbilityOne Commission"),
    ("Census Bureau", "Bureau of the Census"),
    ("Office of the Secretary and Joint Staff", "Joint Chiefs of Staff"),
    ("Department of the Air Force - Headquarters/ICIO (FOIA)",
        "U.S. Air Force"),
    ("Department of the Army - Freedom of Information and Privacy Office",
        "U.S. Army"),
    ("Department of the Navy - Main Office", "U.S. Navy"),
    ("Marine Corps - FOIA Program Office (ARSF)", "U.S. Marines"),
    ('Federal Bureau of Prisons', 'Bureau of Prisons'),
    ('Office of Community Oriented Policing Services',
        'Community Oriented Policing Services'),
    ('Center for Medicare and Medicaid Services',
        'Centers for Medicare and Medicaid Services'),
    ('Department of Housing and Urban Development',
        'Department of Housing and Urban Development'),
    ('AMTRAK', 'National Railroad Passenger Corporation'),
    ('Jobs Corps', 'Job Corps'),
    ('INTERPOL-United States National Central Bureau',
        'U.S. National Central Bureau - Interpol'),
    (' Activity', ''),
    (' - Headquarters', ''),
    ('U.S.', ''),
    ('United States', ''),
    (' & ', ' and '),
    ('Bureau', ''),
    ('Committee for ', ''),
    ('Office of the ', ''),
    (' of the ', ' of '),
    (' for the District of Columbia', ''),
]


def clean_name(name):
    """ Cleans name to try to match it with names in yaml files """

    name = ACRONYM.sub('', name)
    for item, replacement in REPLACEMENTS:
        if item in name:
            name = name.replace(item, replacement)
    return name.strip(' ')


def extract_abbreviation(name):
    """ Extract abbreviation from name string """

    match = ACRONYM.search(name)
    abbreviation = None
    if match:
        abbreviation = match.group(0).strip("() ")
    return name, abbreviation


def transform_json_data(data):
    """ Create a dictionary with name as key to allow for easy searching """

    new_dict = {}
    for contact_data in data:
        if contact_data['Language'] == "en":
            name, abbreviation = extract_abbreviation(
                name=contact_data['Name'])
            name = clean_name(name=name)
            new_dict[name] = {'usa_id': contact_data['Id']}
            if abbreviation:
                new_dict[name].update({'abbreviation': abbreviation})
            description = contact_data.get('Description')
            if description:
                new_dict[name].update({'description': description})
    return new_dict


def update_dict(old_data, new_data):
    """
    Overwrites old usa_ids, descriptions, and abbreviation with data from
    the USA contacts API
    """

    old_data['usa_id'] = new_data['usa_id']
    if new_data.get('description'):
        old_data['description'] = new_data['description']
    if new_data.get('abbreviation'):
        old_data['abbreviation'] = new_data['abbreviation']
    return old_data


def write_yaml(filename, data):
    """ Exports the updated yaml file """

    with open(filename, 'w') as f:
        f.write(yaml.dump(
            data, default_flow_style=False, allow_unicode=True))


def get_api_data():
    """ Retrives data from USA Gov Contacts API """

    client = CachedSession('usa_contacts')
    data = client.get(USA_CONTACTS_API)
    data = transform_json_data(data=data.json()['Contact'])
    return data


def patch_yamls():
    """
    Loops through yaml files and matches them to USA contacts API data
    """

    data = get_api_data()
    for filename in glob("data" + os.sep + "*.yaml"):
        with open(filename) as f:
            agency = yaml.load(f.read())
        agency_name = clean_name(agency.get('name'))
        if agency_name in data:
            agency = update_dict(agency, data[agency_name])
            del data[agency_name]
        for office in agency['departments']:
            office_name = clean_name(office['name'])
            if office_name in data:
                office = update_dict(office, data[office_name])
        write_yaml(filename=filename, data=agency)


if __name__ == "__main__":
    patch_yamls()
