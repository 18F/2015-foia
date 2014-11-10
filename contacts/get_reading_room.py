import os
import sys
from urllib.parse import urljoin, urlparse

import requests
import yaml
from glob import glob
from bs4 import BeautifulSoup

from scraper import agency_yaml_filename

def read_yaml_file(agency_abbr):
    yaml_filename = agency_yaml_filename('data', agency_abbr)
    if os.path.exists(yaml_filename):
        agency_data = yaml.load(open(yaml_filename, 'r'))
        return agency_data

def get_base_url(url):
    parsed_uri = urlparse(url)
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    return domain

def domains_match(website_url, reading_room_url):
    website_parsed = urlparse(website_url)
    reading_room_parsed = urlparse(reading_room_url)
    return website_parsed.netloc == reading_room_parsed.netloc
        

def get_absolute_url(link, url):
    href = link.get('href')
    if href and not href.startswith('#'):
        if not href.startswith('http'):
            href = urljoin(url, href)
            if href == get_base_url(url):
                return None
        if domains_match(url, href):
            return (link.text.strip(), href)

def unique_links(links):
    redirected = []
    for l in links:
        response = requests.get(l[1])
        if len(response.history) > 0:
            if response.history[0].status_code == 301:
                redirected.append(
                    (l[0], response.history[0].headers['Location']))
        else:
            redirected.append(l)
            
    seen = set()
    uniques = [l for l in redirected if l[1] not in seen and not seen.add(l[1])]
    return uniques
    
def process(data):
    if 'website' in data and data['website'].strip():
        try:
            response = requests.get(data['website'], verify=False)
        except requests.exceptions.MissingSchema:
            with_schema = 'http://%s' % data['website']
            response = requests.get(with_schema, verify=False)

        if response.status_code == 200:
            doc = BeautifulSoup(response.content)
            all_as = doc.find_all('a')
            counter = 0
            links = set()
            for link in all_as:
                for keyword in ['foia library', 'freedom of information library', 'reading room', 'vault']:
                    if keyword in link.text.lower():
                        url_pair = get_absolute_url(link, data['website'])
                        if url_pair:
                            links.add(url_pair)
            links = unique_links(links)
            if len(links) > 1:
                print(data['website'])
                print(len(links))
                print(links)
                print('--------------')
            
        

def reading_room(agency_abbr):
    agency_data = read_yaml_file(agency_abbr)
    if agency_data:
        process(agency_data)

        if 'departments' in agency_data:
            for department in agency_data['departments']:
                process(department)
        

if __name__ == "__main__":
    agency_abbr = None
    if len(sys.argv) > 1:
        agency_abbr = sys.argv[1]

    if agency_abbr:
        reading_room(agency_abbr)
