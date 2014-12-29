#!/usr/bin/env python
from bs4 import BeautifulSoup
from copy import deepcopy
import logging
from glob import glob
import os
import csv
import re
import requests
import yaml

""" This script scrapes processing times data from foia.gov and dumps
    the data in both the yaml files and `request_time_data.csv`."""

PROCESSING_TIMES_URL = "http://www.foia.gov/foia/Services/DataProcessTime.jsp"
YEARS_URL = 'http://www.foia.gov/data.html'

def load_mapping():
    """
    Opens yaml mapping file and creates a mapping key to translate from
    foia.gov/data names to yaml data names for each year. Both key and
    value are formatted as `name_filename_year`.
    """

    key = {}
    years = get_years()
    with open('layering_data/foiadata_to_yaml_mapping.yaml', 'r') as f:
        mapping = yaml.load(f.read())
    for element in mapping:
        for year in years:
            yaml_name = "{0}_{1}".format(element, year).lower()
            for name in mapping[element]:
                foia_name = "{0}_{1}".format(name, year)
                if not key.get(foia_name):
                    key[foia_name] = [yaml_name]
                else:
                    key[foia_name].append(yaml_name)
    return key


def apply_mapping(data):
    """ Applies mapping to make foia.gov data compatiable with yaml data """

    mapping = load_mapping()
    for foia_data_name in mapping.keys():
        if foia_data_name in data.keys():
            for yaml_name in mapping[foia_data_name]:
                data[yaml_name] = deepcopy(data[foia_data_name])
    return data


def delete_empty_data(data):
    """ Deletes any items with the value `NA` or '' a dictionary """

    keys = list(data.keys())
    for key in keys:
        if data[key] == '':
            del data[key]
    return data


def clean_data(data):
    """
    Deletes agency, year, and component attributes, which are not
    added to the yamls and also any attributes with empty values
    """
    if data.get('agency'):
        del data['agency'], data['year'], data['component']
    return delete_empty_data(data)


def append_time_stats(yaml_data, data, yaml_key, year):
    """ Appends request time stats to list under key request_time_stats"""

    if not yaml_data.get('request_time_stats'):
        yaml_data['request_time_stats'] = {}
    cleaned_data = clean_data(data[yaml_key])
    if cleaned_data:
        yaml_data['request_time_stats'][year.strip("_")] = \
            deepcopy(cleaned_data)
    return yaml_data


def patch_yamls(data):
    """ Patches yaml files with average times """

    years = get_years()
    for filename in glob("data" + os.sep + "*.yaml"):
        short_filename = '_%s' % filename.strip('.yaml').strip('/data')
        with open(filename) as f:
            yaml_data = yaml.load(f.read())
        for year in years:
            year = "_%s" % year
            agency_key = yaml_data['name'] + short_filename + year
            agency_key = agency_key.lower()
            if agency_key in data.keys():
                yaml_data = append_time_stats(
                    yaml_data, data, agency_key, year)
                del data[agency_key]
            for internal_data in yaml_data['departments']:
                office_key = internal_data['name'] + short_filename + year
                office_key = office_key.lower()
                if office_key in data.keys():
                    internal_data = append_time_stats(
                        internal_data, data, office_key, year)
                    del data[office_key]

        with open(filename, 'w') as f:
            f.write(yaml.dump(
                yaml_data, default_flow_style=False, allow_unicode=True))


def make_column_names():
    '''Generates column names'''

    columns = ['year', 'agency']
    kinds = ['simple', 'complex', 'expedited_processing']
    measures = ['average', 'median', 'lowest', 'highest']
    names = []
    for kind in kinds:
        for measure in measures:
            names.append('{0}_{1}_days'.format(kind, measure))
    columns.extend(names)
    return columns


def get_row_data(key, row_data, column_names):
    """
    Collects row data using column names while cleaning up
    anything after the _s
    """

    data = [re.sub("_.*", "", key)]
    for column in column_names:
        data.append(row_data.get(column))
    return data


def write_csv(data):
    """ Writes data to csv """

    column_names = make_column_names()
    with open('request_time_data.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['name'] + column_names)
        for key in sorted(data.keys()):
            writer.writerow(get_row_data(key, data[key], column_names))


def clean_html(html_text):
    """ Converts <1 to 1 in html text"""

    return html_text.replace("><1<", ">less than 1<")


def clean_names(columns):
    '''Standardizes attribute names'''

    clean_columns = []
    for column in columns:
        column = re.sub(' No. of ', ' ', column)
        column = re.sub('-| ', '_', column).lower()
        clean_columns.append(column)
    return clean_columns


def fetch_page(url, params):
    """
    Returns a cached agency processing time page if it exists,
    otherwise the function creates a cache and returns the html.
    """

    filename = "html/{0}_{1}_timedata.html"
    filename = filename.format(
        params.get('agencyName', "all"), params['requestYear'])
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            return f.read()
    else:
        response = requests.get(url, params=params)
        with open(filename, 'w') as f:
            f.write(response.text)
        return response.text


def zip_and_clean(columns, row):
    """ Converts 0 and Nones to NAs and zips together a row and columns """
    data = dict(zip(columns, row))
    if data.get(''):
        del data['']
    return data


def get_key_values(row_items, columns, year, title):
    """ Parses through each table row and returns a key-value pair """

    row_array = []
    for item in row_items:
        if item.span:
            row_array.append(item.span.text)
        else:
            row_array.append(item.text)
    value = zip_and_clean(columns, row_array)
    key = title + "_%s" % value['agency'] + "_%s" % year
    key = key.lower()
    return key, value


def parse_html(html, params, data):
    """ Gets, caches, and parses html from foia.gov """

    soup = BeautifulSoup(clean_html(html))
    year = params['requestYear']
    table = soup.find("table", {"id": "agencyInfo0"})
    columns = clean_names([column.text for column in table.findAll("th")])
    for row in table.findAll("tr"):
        row_items = row.findAll("td")
        if len(row_items) > 2:
            title = row.findAll('span')[1].attrs['title']
            key, value = get_key_values(row_items, columns, year, title)
            data[key] = value
    return data


def get_years(html=None):
    """ Gets year data by scraping the data page """

    if html is None:
        r = requests.get(YEARS_URL)
        html = r.text

    soup = BeautifulSoup(html)
    boxes = soup.findAll("input", {"type": "checkbox"})
    years = []
    for box in boxes:
        years.extend(re.findall('\d+', box.attrs.get('name', 'Nothing')))
    return(list(set(years)))


def all_years(url, params, data):
    """ Loops through yearly data """

    for year in get_years():
        params["requestYear"] = year
        html = fetch_page(url, params)
        data = parse_html(html, params, data)
    return data


def scrape_times():
    """ Loops through foia.gov data for processing time """

    url = PROCESSING_TIMES_URL
    params = {"advanceSearch": "71001.gt.-999999"}
    data = {}
    data = all_years(url, params, data)
    logging.info("compelete: %s", params.get('agencyName', "all"))
    agencies = set([value['agency'] for value in data.values()])
    for agency in agencies:
        params["agencyName"] = agency
        data = all_years(url, params, data)
        logging.info("compelete: %s", params.get('agencyName', "all"))
    data = apply_mapping(data)
    write_csv(data)
    patch_yamls(data)


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)
    scrape_times()
