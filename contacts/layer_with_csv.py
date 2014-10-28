#!/usr/bin/env python

"""Fill in any blanks in the YAML files by investigating a XLS"""
from copy import deepcopy
from glob import glob
import logging
import os
import re
from urllib.request import urlopen

import xlrd
import yaml

FIX_AGENCY_NAME = re.compile("\s+$")

def address_lines(row):
    """Convert a row of dictionary data into a list of address lines"""
    lines = []
    if row['Room Number']:
        lines.append(row['Room Number'])
    if row['Street Address']:
        lines.append(row['Street Address'])
    if row['City'] and row['State'] and row['Zip Code']:
        lines.append(row['City'] + ', ' + row['State'] + ' '
                     + str(row['Zip Code']))
    return lines


def contact_string(row):
    """Pull out contact name and/or phone number from a row"""
    contact = row['Name']
    if row['Telephone']:
        if contact:
            contact += ', '
        contact += 'Phone: ' + row['Telephone']
    return contact


def add_contact_info(contacts, row):
    """Process a row of the xls, adding data to the contacts dictionary"""
    agency, office = row['Department'], FIX_AGENCY_NAME.sub('',row['Agency'])

    if agency not in contacts:
        contacts[agency] = {}
    if office not in contacts[agency]:
        contacts[agency][office] = {'misc': {}, 'emails': []}
    office_struct = contacts[agency][office]

    if row['Website'] in ('http://', 'https://'):
        row['Website'] = ''
    for row_name, field_name in (('Online Request Form', 'request_form'),
                                 ('Fax', 'fax'), ('Notes', 'notes'),
                                 ('Telephone', 'phone'),
                                 ('Website', 'website')):
        if row[row_name].strip():
            office_struct[field_name] = row[row_name]
    address = address_lines(row)
    if address and 'address' not in office_struct:
        office_struct['address'] = address
    if row['Email Address']:
        office_struct['emails'].append(
            row['Email Address'].replace('mailto:', ''))

    #   People
    lower_title = row['Title'].lower()
    processed = False
    for title_text in ('service center', 'public liaison', 'foia officer'):
        if title_text in lower_title:
            field_name = title_text.replace(' ', '_')
            office_struct[field_name] = contact_string(row)
            processed = True
    if not processed and row['Title']:
        office_struct['misc'][row['Title']] = contact_string(row)


def contacts_from_xls():
    """Generate a lookup structure from the XLS files hosted by foia.gov. This
    is a dictionary of this form:
    { "agency_name": { "office_name": {dict-corresponding-to-yaml} } }
    Look in local directories before pulling down the data."""
    contacts = {}

    if not os.path.isdir("xls"):
        os.mkdir("xls")
    xls_path = "xls" + os.sep + "full-foia-contacts.xls"
    if not os.path.isfile(xls_path):
        with open(xls_path, 'wb') as f:
            data = urlopen("http://www.foia.gov/full-foia-contacts.xls")
            f.write(data.read())
    workbook = xlrd.open_workbook(xls_path)
    for sheet in workbook.sheet_names():
        sheet = workbook.sheet_by_name(sheet)
        field_names = [sheet.cell_value(0, x) for x in range(sheet.ncols)]
        for row_idx in range(0, sheet.nrows):
            row = {field_names[x]: sheet.cell_value(row_idx, x)
                   for x in range(sheet.ncols)}
            add_contact_info(contacts, row)
    return contacts


def patch_dict(old_dict, new_dict):
    """Merge the new dict onto the old, only replacing a field if it did not
    exist in the original. A bit more complexity on the 'misc' fields. Returns
    a new dict if changes were made or None if not"""
    changed = False
    to_return = deepcopy(old_dict)
    for field in new_dict:
        if new_dict[field] and field not in old_dict:
            to_return[field] = new_dict[field]
            changed = True
    if 'misc' in new_dict and 'misc' in old_dict:
        misc = patch_dict(old_dict['misc'], new_dict['misc'])
        if misc:
            to_return['misc'] = misc
            changed = True
    if changed:
        return to_return


def patch_yaml():
    """Compare YAML files with fields in the XLS. Update the YAML files with
    any information they are missing."""
    contacts = contacts_from_xls()
    for filename in glob("data" + os.sep + "*.yaml"):
        with open(filename) as f:
            yaml_data = yaml.load(f.read())
        if yaml_data['name'] in contacts:
            contact_data = contacts[yaml_data['name']]
            departments, new_dept_count = [], 0
            for yaml_office in yaml_data['departments']:
                if yaml_office['name'] in contact_data:
                    contact_office = contact_data[yaml_office['name']]
                    dept = patch_dict(yaml_office, contact_office)
                    if dept:
                        new_dept_count += 1
                    else:
                        dept = yaml_office
                    departments.append(dept)
                else:
                    logging.warning('Not in XLS: %s -> %s',
                                    yaml_data['name'], yaml_office['name'])
            if new_dept_count > 0:
                yaml_data['departments'] = departments
                with open(filename, 'w') as f:
                    f.write(yaml.dump(yaml_data, default_flow_style=False,
                                      allow_unicode=True))
                    logging.info('Rewrote %s with %s updated departments',
                                 filename, new_dept_count)
        else:
            logging.warning('Not in XLS: %s', yaml_data['name'])

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    patch_yaml()
