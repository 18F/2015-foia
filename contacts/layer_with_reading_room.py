import os
import sys
from urllib.parse import urljoin, urlparse

import requests
import yaml
from bs4 import BeautifulSoup

from scraper import agency_yaml_filename, AGENCIES
from scraper import save_agency_data


def read_yaml_file(agency_abbr):
    yaml_filename = agency_yaml_filename('data', agency_abbr)
    if os.path.exists(yaml_filename):
        agency_data = yaml.load(open(yaml_filename, 'r'))
        return agency_data


def get_base_url(url):
    """ Given a long text url, with sub-directories, query parameters, just
    return the base URL for the domain. """

    parsed_uri = urlparse(url)
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    return domain


def domains_match(website_url, reading_room_url):
    website_parsed = urlparse(website_url)
    reading_room_parsed = urlparse(reading_room_url)
    return website_parsed.netloc == reading_room_parsed.netloc


def clean_link_text(link_text):
    """ The link text sometimes contains new lines, or extrananeous spaces, we
    remove them here. """

    return link_text.strip().replace('\n', '').replace('\r', '')


def get_absolute_url(link, url):
    href = link.get('href')
    if href and not href.startswith('#'):
        if not href.startswith('http'):
            href = urljoin(url, href)
            if href == get_base_url(url):
                return None
        if domains_match(url, href):
            return [clean_link_text(link.text), href]


def unique_links(links):
    """ We sometimes get the same URI with different link texts. Squash those.
    """

    redirected = []
    for l in links:
        try:
            response = requests.get(l[1], verify=False)
            if len(response.history) > 0:
                if response.history[0].status_code == 301:
                    redirected.append(
                        [l[0], response.history[0].headers['Location']])
            else:
                redirected.append(l)
        except requests.exceptions.ConnectionError:
            # Ignore the link, as it clearly doesn't work.
            pass
        except requests.exceptions.TooManyRedirects:
            # Ignore the link, as it clearly doesn't work.
            pass

    seen = set()
    uniques = [l for l in redirected
               if l[1] not in seen and not seen.add(l[1])]
    return uniques


def scrape_reading_room_links(content, website_url):
    doc = BeautifulSoup(content)
    all_as = doc.find_all('a')
    links = []
    for link in all_as:
        for keyword in [
                'foia library',
                'freedom of information library',
                'reading room', 'vault']:
            if keyword in link.text.lower()\
                    and 'certification' not in link.text.lower():
                url_pair = get_absolute_url(link, website_url)
                if url_pair:
                    links.append(url_pair)
    return links


def process(data):
    """ Actually scrape and clean up the reading room or library links. """

    if 'website' in data and data['website'].strip():
        try:
            response = requests.get(data['website'], verify=False)
        except requests.exceptions.MissingSchema:
            with_schema = 'http://%s' % data['website']
            response = requests.get(with_schema, verify=False)
        except:
            return None

        if response.status_code == 200:
            links = scrape_reading_room_links(
                response.content, data['website'])
            links = unique_links(links)
            if len(links) == 0:
                return None
            return links


def uniquefy(links):
    seen = set()
    uniques = [l for l in links
               if l[1] not in seen and not seen.add(l[1])]
    return uniques


def update_links(agency_data, links):
    """ Update the reading rooms links for a particular agency. """

    agency_data = dict(agency_data)

    original_links = agency_data.get('reading_rooms', [])
    all_links = original_links + links
    unique_links = uniquefy(all_links)
    sorted_uniques = sorted(unique_links, key=lambda x: x[0])

    agency_data['reading_rooms'] = sorted_uniques
    return agency_data


def reading_room(agency_abbr):
    """ Get the reading room links for the agency, and also for each of the
    departments. """

    agency_data = read_yaml_file(agency_abbr)
    if agency_data:
        links = process(agency_data)
        if links:
            agency_data = update_links(agency_data, links)
        departments = []
        if 'departments' in agency_data:
            for department in agency_data['departments']:
                links = process(department)
                if links:
                    department = update_links(department, links)
                departments.append(department)
            agency_data['departments'] = departments
        return agency_data


def all_reading_rooms():
    """ Get reading room links for ALL agencies. """

    for agency in AGENCIES:
        agency_data = reading_room(agency)
        save_agency_data(agency, agency_data)


if __name__ == "__main__":
    agency_abbr = None
    if len(sys.argv) > 1:
        agency_abbr = sys.argv[1]

    if agency_abbr:
        reading_room(agency_abbr)
    else:
        all_reading_rooms()
