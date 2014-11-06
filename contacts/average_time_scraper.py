#!/usr/bin/env python
from urllib.request import urlopen
from lxml import html
import logging
from glob import glob
import yaml
import os
import csv
import re
import requests

def patch_yamls(data):
    """patches yaml files with average times"""
    matches = 0
    for filename in glob("data" + os.sep + "*.yaml"):
        short_filename = '_%s' % filename.strip('.yaml').strip('/data')
        with open(filename) as f:
            yaml_data = yaml.load(f.read())
            print(yaml_data['name']+"_2013" + short_filename)
            if yaml_data['name']+"_2013" + short_filename in data.keys():
                matches += 1
                yaml_data['simple_request_processing_time_mean_days'] = \
                    data[yaml_data['name']+"_2013" + short_filename]\
                        .get('Simple-Average No. of Days')
                yaml_data['simple_request_processing_time_median_days'] = \
                    data[yaml_data['name']+"_2013" + short_filename]\
                        .get('Simple-Median No. of Days')

        for internal_data in yaml_data['departments']:
            if internal_data['name']+"_2013" + short_filename in data:
                matches += 1
                internal_data['simple_request_processing_time_mean_days'] = \
                    data[internal_data['name']+"_2013" + short_filename]\
                        .get('Simple-Average No. of Days')
                internal_data['simple_request_processing_time_median_days'] = \
                    data[internal_data['name']+"_2013" + short_filename]\
                        .get('Simple-Median No. of Days')

        with open(filename, 'w') as f:
            f.write(yaml.dump(
                yaml_data, default_flow_style=False, allow_unicode=True))
    print(matches )


def write_csv(data):
    '''write data to csv'''

    with open('request_time_data.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['name','year','agency','simple_average',
                        'simiple_median','expedited_average',
                        'expedited_median','complex_average',
                        'complex_median'])
        for element in data.items():
            writer.writerow([
                re.sub("_.*","",element[0]),
                element[1].get('Year','NA'),
                element[1].get('Agency','NA'),
                element[1].get('Simple-Average No. of Days','NA'),
                element[1].get('Simple-Median No. of Days','NA'),
                element[1].get('Expedited Processing-Average No. of Days','NA'),
                element[1].get('Expedited Processing-Median No. of Days','NA'),
                element[1].get('Complex-Average No. of Days','NA'),
                element[1].get('Complex-Median No. of Days','NA')
                ])


def get_html(url, params):
    '''pull cached html if exists, else creates html file cache'''

    filename = "html/{0}_{1}_timedata.html"
    filename = filename.format(params.get('agencyName',"all"),
        params['requestYear'])
    if os.path.isfile(filename):
         with open(filename, 'r') as f:
            return f.read()
    else:
        response = requests.get(url,params=params)
        with open(filename, 'w') as f:
            f.write(response.text)
        return response.text

def zero_to_na(element):
    '''converts all zeros to string'''

    if element == '0':
        return 'NA'
    else:
        return str(element)

def zip_and_clean(header,row):
    '''also converts 0 to NAs and zips together a row and header'''

    return dict(zip(header, map(zero_to_na, row)))

def get_agency(value):
    return '_%s' % value['Agency']

def parse_table(url, params, data):
    '''gets, caches, and parses url to extract the table data'''

    tree = html.fromstring(get_html(url,params))
    if tree.xpath('//table//tr//th//a') == []:
        return data
    header=[col.text for col in tree.xpath('//table//tr//th//a')]
    year = '_%s' % params['requestYear']
    for row in tree.xpath('//table//tr[not(th)]'):
        value = zip_and_clean(header, row.xpath('.//td//text()'))
        key = row.xpath('.//span[@title]')[1].values()[0] + year + \
            get_agency(value)
        data[key] = value
    return data


def all_years(url, params, data):
    '''loops through yearly data'''

    years = ['2013','2012','2011','2010','2009','2008']
    for year in years:
        params["requestYear"] = year
        data = parse_table(url, params, data)
    return data


def scrape_times():
    '''loop through foia.gov data for processing time'''

    url = "http://www.foia.gov/foia/Services/DataProcessTime.jsp"
    params = {"advanceSearch":"71001.gt.-999999"}
    data = {}
    data = all_years(url, params, data)
    logging.info("compelete: %s",params.get('agencyName',"all"))
    agencies = set([value['Agency'] for value in data.values()])
    for agency in agencies:
        params["agencyName"] = agency
        data = all_years(url, params, data)
        logging.info("compelete: %s",params.get('agencyName',"all"))
    write_csv(data)
    patch_yamls(data)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scrape_times()
