from glob import glob
import os
import csv
import yaml
from slugify import slugify


def load_csv_data():
    ''' loads mapping of yamls to foia.gov data'''

    key = {}
    with open('manual_data_sheet.csv', 'r') as csvfile:
        datareader = csv.reader(csvfile)
        for row in datareader:
            key[row[1]] = row
    return key


def cap_length(s, l):
    return s if len(s) <= l else s[0:l]


def get_if_exists(filename):
    if os.path.isfile(filename):
        with open(filename) as f:
            return yaml.load(f.read())
    else:
        return {}


def insert_data(old_data, new_data, agency, office=None):

    if not office:
        if not old_data.get('name'):
            old_data['name'] = agency
        old_data['request_form'] = new_data[3]
        return old_data

    if office:
        if not old_data.get('departments'):
            old_data['departments'] = \
                [{'name': office, 'request_form': new_data[3]}]
            return old_data
        else:
            for department in old_data.get('departments'):
                if department['name'] == office:
                    department['request_form'] = new_data[3]
                    return old_data
            old_data['departments'].append(
                {'name': office, 'request_form': new_data[3]})
            return old_data


def patch_yamls():
    """Patches yaml files with average times"""
    data = load_csv_data()
    print (len(data.keys()))
    counter = 0
    for filename in glob("data" + os.sep + "*.yaml"):
        with open(filename) as f:
            yaml_data = yaml.load(f.read())
        manual_data = get_if_exists(
            filename.replace('data', 'manual_data'))
        agency_slug = slugify(yaml_data['name'].replace('.', ''))
        if agency_slug in data.keys():
            manual_data = insert_data(
                manual_data, data[agency_slug], yaml_data['name'])
            counter += 1
        for internal_data in yaml_data['departments']:
            office_slug = cap_length(
                slugify(internal_data['name'].replace('.', '')), 50)
            if agency_slug + "--" + office_slug in data.keys():
                manual_data = insert_data(
                    manual_data,
                    data[agency_slug + "--" + office_slug],
                    yaml_data['name'], internal_data['name'])
                counter += 1
        if manual_data != {}:
            with open(filename.replace('data', 'manual_data'), 'w') as f:
                f.write(yaml.dump(
                    manual_data, default_flow_style=False, allow_unicode=True))
    print(counter)


if __name__ == "__main__":
    patch_yamls()
