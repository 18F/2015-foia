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

# The tuples below are used to normalize the names between the naming
# convention of the data/yaml files and the naming convention of the
# USA Contacts API (http://www.usa.gov/api/USAGovAPI/contacts.json/contacts)
REPLACEMENTS = (
    ("Purchase from People Who Are Blind or Severely Disabled",
        "U.S. AbilityOne Commission"),
    ("Office of the Secretary and Joint Staff", "Joint Chiefs of Staff"),
    ("Department of the Army - Freedom of Information and Privacy Office",
        "U.S. Army"),
    ('Federal Bureau of Prisons', 'Bureau of Prisons'),
    ('Office of Community Oriented Policing Services',
        'Community Oriented Policing Services'),
    ('AMTRAK', 'National Railroad Passenger Corporation'),
    ('Jobs Corps', 'Job Corps'),
    ('INTERPOL-United States National Central Bureau',
        'U.S. National Central Bureau - Interpol'),
    ('Center for', 'Centers for'),
    (' for the District of Columbia', ''),
    (' - FOIA Program Office', ''),
    (' - Main Office', ''),
    (' Activity', ''),
    (' - Headquarters Office', ''),
    (' - Headquarters', ''),
    ('U.S.', ''),
    ('United States', ''),
    (' & ', ' and '),
    ('Bureau', ''),
    ('Committee for ', ''),
    ('Office of the ', ''),
    ('/ICIO', ''),
    (' of the ', ' of '),
    ('Department of ', ''),
)


def clean_name(name):
    """ Cleans name to try to match it with names in yaml files """

    name = ACRONYM.sub('', name)
    for item, replacement in REPLACEMENTS:
        name = name.replace(item, replacement)
    return name.strip(' ')


def extract_abbreviation(name):
    """ Extract abbreviation from name string """

    match = ACRONYM.search(name)
    if match:
        return match.group(0).strip("() ")


def create_contact_dict(data):
    """
    Generates a dictionary containing a USA Contacts API ID, description, and
    abbreviation when possible
    """

    new_dict = {'usa_id': data['Id']}
    abbreviation = extract_abbreviation(name=data['Name'])
    if abbreviation:
        new_dict['abbreviation'] = abbreviation
    description = data.get('Description')
    if description:
        new_dict['description'] = description
    return new_dict


def transform_json_data(data):
    """
    Reformats data into a dictionary with name as key to allow for
    easy matching to yaml files. This script also ensures that only
    English language descriptons are stored in the yaml files.
    """

    new_dict = {}
    for contact_data in data:
        # Limits descriptions to only English Language.
        if contact_data['Language'] == "en":
            cleaned_name = clean_name(name=contact_data['Name'])
            new_dict[cleaned_name] = create_contact_dict(data=contact_data)
            synonyms = contact_data.get('Synonym')
            if synonyms:
                for synonym in synonyms:
                    cleaned_synonym = clean_name(name=synonym)
                    new_dict[cleaned_synonym] = new_dict.get(cleaned_name)
    return new_dict


def update_dict(old_data, new_data):
    """
    Overwrites old usa_ids, descriptions, and abbreviation with data from
    the USA contacts API
    """

    old_data['usa_id'] = new_data.get('usa_id')
    if new_data.get('description') and not old_data.get('description'):
        old_data['description'] = new_data.get('description')
    if new_data.get('abbreviation') and not old_data.get('abbreviation'):
        old_data['abbreviation'] = new_data['abbreviation']
    return old_data


def write_yaml(filename, data):
    """ Exports the updated yaml file """

    with open(filename, 'w') as f:
        f.write(yaml.dump(
            data, default_flow_style=False, allow_unicode=True))


def patch_yamls(data, directory):
    """
    Loops through yaml files and matches them to USA contacts API data
    """

    for filename in glob(directory):
        with open(filename) as f:
            agency = yaml.load(f.read())
        agency_name = clean_name(agency.get('name'))
        if agency_name in data:
            agency = update_dict(agency, data[agency_name])
        for office in agency['departments']:
            office_name = clean_name(office['name'])
            if office_name in data:
                office = update_dict(office, data[office_name])
        yield agency, filename


def get_api_data(url, cache):
    """ Retrives data from USA Gov Contacts API """

    client = CachedSession(cache)
    request = client.get(url)
    data = request.json().get('Contact')
    if not data:
        data = [request.json()]
    data = transform_json_data(data)
    return data


def layer_with_data():
    """ This function layers the data/yaml files with USA Contacts API data """

    data = get_api_data(url=USA_CONTACTS_API, cache='usa_contacts')
    for updated_yaml, filename in patch_yamls(
            data=data, directory="data" + os.sep + "*.yaml"):
        write_yaml(filename=filename, data=updated_yaml)


if __name__ == "__main__":
    layer_with_data()
