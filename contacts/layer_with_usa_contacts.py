#!/usr/bin/env python

import yaml
import xlrd
import os
import json
from glob import glob
import re
import logging

""" Update YAML files with usa_id, description, and acronyms. """

ACRONYM_FINDER = re.compile('\((.*?)\)')
extract_names = lambda yaml_data: [dept['name'] for dept in yaml_data]


def float_to_int_str(number):
    """converts input to ints and then to strings to clean xls data"""
    try:
        return str(int(float(number)))
    except:
        return number


def extract_acronym(usa_name):
    """extracts acronyms from a string if there is one"""
    acronym_list = ACRONYM_FINDER.findall(usa_name)
    if len(acronym_list) == 1:
        return acronym_list[0]
    elif len(acronym_list) == 0:
        return ""
    else:
        return "Massive Error"


def load_all_usa_data():
    """loads data from all_usa_data.json file """
    with open('usagov-data/all_usa_data.json', 'r') as f:
        all_usa_data = json.loads(f.read())
    data = {}
    for office in all_usa_data:
        if office.get('Language') == "en":

            data[office['Name']] = {
                'description': office.get('Description', 'No Description'),
                'id': office.get('Id', 'No Id'),
                'acronym_usa_contacts': extract_acronym(office['Name'])}
    return data


def load_usacontacts():
    """Loads data from usacontacts.xls """
    data = {}
    xls_path = "usagov-data/foiaHub-usaContacts-matches.xlsx"
    workbook = xlrd.open_workbook(xls_path)
    sheet = workbook.sheet_by_name(workbook.sheet_names()[0])
    header_names = [sheet.cell_value(0, i) for i in range(sheet.ncols)]
    for row_num in range(1, sheet.nrows):
        row = {
            header_names[i]: sheet.cell_value(row_num, i)
            for i in range(sheet.ncols)}
        row['usa_id'] = float_to_int_str(row['usa_id'])

        if row.get('description',"No Description") == "":
            row['description'] = "No Description"
        data[row['fh_name']] = row
    return data


def merge_data():
    """Merges usacontacts.xls and all_usa_data.json"""
    usacontacts = load_usacontacts()
    all_usa_data = load_all_usa_data()
    for name_usacontacts in usacontacts:
        found = False
        # try to match on names and add description if there is none
        if name_usacontacts in all_usa_data.keys():
            usacontacts[name_usacontacts]['description'] = \
                all_usa_data[name_usacontacts]['description']
            found = True
        # try to match on ids and add description if there is none
        if not found:
            current_id = usacontacts[name_usacontacts]['usa_id']
            for name in all_usa_data.keys():
                if all_usa_data[name]['id'] == current_id:
                    usacontacts[name_usacontacts]['description'] = \
                        all_usa_data[name]['description']
                    break
    return usacontacts

def replace_description(yaml_data):
    name = yaml_data['name']
    for department in yaml_data['departments']:
        if name == department['name']:
            department['description'] = yaml_data['description']
            break
    return yaml_data


def clean_yaml(yaml_data):
    """ clean yaml file of ids, descriptions, and abbreviation"""
    if 'usa_id' in yaml_data.keys():
        del yaml_data['usa_id']
    if 'abbreviation' in yaml_data.keys():
        del yaml_data['abbreviation']
    if 'description' in yaml_data.keys():
        yaml_data = replace_description(yaml_data)
        del yaml_data['description']
    return yaml_data

def update_dict(old_dict,new_dict):
    """merge the data in the yaml files with the merged data
    overwrites ids, acronyms, but not descriptions"""
    if new_dict[old_dict['name']]['usa_id'] != '':
        old_dict['usa_id'] = new_dict[old_dict['name']]['usa_id']

    if new_dict[old_dict['name']]['acronym'] != "None":
        old_dict['abbreviation'] =\
            new_dict[old_dict['name']]['acronym']

    if 'description' not in old_dict.keys() or \
            old_dict['description'] == "No Description":
        old_dict['description'] = new_dict[old_dict['name']].get(
            'description', "No Description")

    logging.info("%s updated", old_dict['name'])
    del new_dict[old_dict['name']]

    return old_dict, new_dict


def patch_yaml():
    """patches yaml files with usa_id, correct acronyms,
    and descriptions if there is none"""
    data = merge_data()
    for filename in glob("data" + os.sep + "*.yaml"):
        with open(filename) as f:
            yaml_data = yaml.load(f.read())
            if yaml_data['name'] in data.keys():
                if yaml_data['name'] in \
                        extract_names(yaml_data['departments']):
                    yaml_data = clean_yaml(yaml_data)
                else:
                    yaml_data,data = update_dict(yaml_data,data)
        for internal_data in yaml_data['departments']:
            if internal_data['name'] in data:
                internal_data,data = update_dict(internal_data,data)
        with open(filename, 'w') as f:
            f.write(yaml.dump(
                yaml_data, default_flow_style=False, allow_unicode=True))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    patch_yaml()
