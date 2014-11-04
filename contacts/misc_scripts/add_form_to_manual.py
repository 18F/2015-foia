#!/usr/bin/env python

import yaml
import xlrd
import os
import json
from glob import glob
import re
import csv
import logging


extract_names = lambda yaml_data: [dept['name'] for dept in yaml_data]


def load_forms_data():
    ''' open from form url form_type.csv'''
    data = {}
    with open('form_type.csv') as csvfile:
        form_list = csv.reader(csvfile)
        for row in form_list:
            data[row[0]] = row[1].strip()
    return data

def load_usacontacts():
    """Loads data from usacontacts.xls """
    form_data = load_forms_data()
    data = {}
    xls_path = "../usagov-data/foiaHub-usaContacts-matches.xlsx"
    workbook = xlrd.open_workbook(xls_path)
    sheet = workbook.sheet_by_name(workbook.sheet_names()[0])
    header_names = [sheet.cell_value(0, i) for i in range(sheet.ncols)]
    for row_num in range(1, sheet.nrows):
        row = {
            header_names[i]: sheet.cell_value(row_num, i)
            for i in range(sheet.ncols)}
        #add all form urls
        request_form = form_data.get(row['fh_name'],"None")
        if "http" in request_form:
            row['request_form'] = request_form
            data[row['fh_name']] = row
    return data

def fix_manual(filename,name,top_level_name,top_level,form):
    filename = re.sub("data","manual_data",filename)
    if os.path.isfile(filename):
         with open(filename) as f:
            yaml_data = yaml.load(f.read())

            if top_level:
                yaml_data['request_form'] = form
            else:
                yaml_data['departments'].append({'name':name,'request_form':form})

    else:
        yaml_data = {}
        if top_level:
            yaml_data['name'] = top_level_name
            yaml_data['request_form'] = form

        else:
            yaml_data['name'] = top_level_name
            yaml_data['departments'] = {'name':name,'request_form':form}

    with open(filename, 'w') as yaml_file:
        yaml_file.write(yaml.dump(
            yaml_data, default_flow_style=False, allow_unicode=True))


def patch_yaml():
    """patches yaml files with usa_id, correct acronyms,
    and descriptions if there is none"""
    data = load_usacontacts()


    for filename in glob("../data" + os.sep + "*.yaml"):
        with open(filename) as f:
            yaml_data = yaml.load(f.read())
            if yaml_data['name'] in data.keys():
                if yaml_data['name'] not in extract_names(yaml_data['departments']):
                    fix_manual(filename,yaml_data['name'],yaml_data['name'],True, data[yaml_data['name']]['request_form'])

        for internal_data in yaml_data['departments']:
            if internal_data['name'] in data:

                fix_manual(filename,internal_data['name'],yaml_data['name'], False,data[internal_data['name']]['request_form'])



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    patch_yaml()
