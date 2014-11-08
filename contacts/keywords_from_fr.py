#!/usr/bin/env python

# Fetch and build keywords from the "subject" field of federal register data

from datetime import date, timedelta
from glob import glob
import itertools
import logging
import re
import os
import string

import requests
from requests_cache.core import CachedSession
import yaml


FR_BASE = "https://www.federalregister.gov"
API_BASE = FR_BASE + "/api/v1/"
FR_ARTICLES = API_BASE + "articles"


def fetch_page(year, month, page_num, client=requests):
    """Download a single page of 1000 results; return the results dict"""
    # Don't use a dict as we need the same order with each request (for
    # caching)
    params = [
        ("conditions[publication_date][gte]", "%d-%02d-01" % (year, month)),
        ("conditions[publication_date][lte]",
         "%d-%02d-%02d" % (year, month, last_day_in_month(year, month))),
        ("fields[]", ["agency_names", "topics"]),
        ("order", "oldest"),
        ("page", page_num),
        ("per_page", 1000),
    ]
    result = client.get(FR_ARTICLES, params=params)
    if result.status_code != 200:
        logging.warning("Received %s on %s-%s (%s)", result.status_code, year,
                        month, page_num)
        return {'results': []}

    try:
        return result.json()
    except ValueError:
        logging.warning("Error converting to json on %s-%s (%s)",
                        year, month, page_num)
        return {'results': []}


def results_from_month(year, month, client=requests):
    """Download a month of documents and emit any agency-topic pairs via a
    generator"""
    page_num = 1
    finished = False
    while not finished:
        finished = True
        results = fetch_page(year, month, page_num, client)
        for result in results['results']:
            agencies = result['agency_names'] or []
            topics = result['topics'] or []
            for pair in itertools.product(agencies, topics):
                yield pair
        if 'next_page_url' in results:
            finished = False
            page_num += 1


def normalize_name(name):
    """The agency names used in the federal register don't always match those
    in the FOIA data. Uppercase everything and strip off any references to the
    US"""
    name = name.split(' - ')[0]
    name = name.upper().strip()
    name = "".join(filter(lambda x: x in (string.ascii_uppercase + " "), name))
    replacements = (('CENTERS', 'CENTER'), ('SERVICES', 'SERVICE'))
    remove = ('UNITED STATES', 'DEPARTMENT', 'OFFICE', 'COMMISSION', 'BUREAU',
              'BOARD', 'AGENCY', 'ADMINISTRATION', 'SERVICE', 'FEDERAL', 'US',
              'AND', 'OF', 'THE', 'FOR', 'ON', 'CFR')
    for old, new in replacements:
        name = re.sub(r'\b' + old + r'\b', new, name)
    for old in remove:
        name = re.sub(r'\b' + old + r'\b', ' ', name)
    while '  ' in name:
        name = name.replace('  ', ' ')
    return name.strip()


def normalize_and_map(keywords):
    """Maps old dictionary to dictionary with new keys without loosing
    keys in the process """
    new_dictionary = dict()
    for key in keywords.keys():
        normal_key = normalize_name(key)
        new_dictionary[normal_key] = \
            keywords.get(key,[]) | set(new_dictionary.get(normal_key,[]))
    return new_dictionary


def add_results(results, keywords):
    """Add entries found in the results to the dictionary of keywords"""
    for result in results['results']:
        agencies = result['agency_names'] or []
        topics = result['topics'] or []
        for agency, topic in itertools.product(agencies, topics):
            if agency not in keywords:
                keywords[agency] = set()
            keywords[agency].add(topic)


def subtract_month(cursor):
    """Timedeltas don't encompass months, so just subtract a day until we hit
    the previous month"""
    original_month = cursor.month
    while cursor.month == original_month:
        cursor = cursor - timedelta(days=1)
    return cursor


def last_day_in_month(year, month):
    """Find the last day in this cursor's month"""
    cursor = date(year, month, 28)
    while cursor.month == month:
        cursor = cursor + timedelta(days=1)
    cursor = cursor - timedelta(days=1)
    return cursor.day


def build_keywords():
    """Hit page after page of FR search results (if not cached). Return a
    dictionary of agency-name mapped to the set of applicable topics."""
    keywords = {}
    today = date.today()
    this_year, this_month = today.year, today.month
    # Do not cache this month as it'll change with each run
    #for agency, topic in results_from_month(this_year, this_month):
    #    if agency not in keywords:
    #        keywords[agency] = set()
    #    keywords[agency].add(topic)

    # Now, step back until 1999 - there are no topics before 2000
    client = CachedSession('fr')
    cursor = subtract_month(today)
    while cursor.year > 1999:
        num_distinct = sum(len(words) for words in keywords.values())
        logging.info("Processing %d-%02d. Num distinct keywords: %d",
                     cursor.year, cursor.month, num_distinct)
        for agency, topic in results_from_month(
                cursor.year, cursor.month, client):
            if agency not in keywords:
                keywords[agency] = set()
            keywords[agency].add(topic)
        cursor = subtract_month(cursor)

    return keywords


def new_keywords(agency_data, fr_keywords):
    """Return the number of new keywords and the (potentially modified) agency
    data"""
    name = normalize_name(agency_data['name'])
    if name in fr_keywords:
        original_keywords = set(agency_data.get('keywords', []))
        keywords = original_keywords | fr_keywords[name]
        return len(keywords), dict(agency_data,
                                   keywords=list(sorted(keywords)))
    return 0, agency_data


def patch_yaml():
    """Go through the YAML files; for all agencies, check if we have some new
    keywords based on FR data. If so, update the YAML"""
    fr_keywords = normalize_and_map(build_keywords())

    for filename in glob("data" + os.sep + "*.yaml"):
        num_new_keywords = 0
        with open(filename) as f:
            yaml_data = yaml.load(f.read())
        # First, check if keywords need to be added to the root
        num_new, modified = new_keywords(yaml_data, fr_keywords)
        if num_new:
            del fr_keywords[normalize_name(yaml_data['name'])]
            yaml_data = modified
            num_new_keywords += num_new

        # Next, check the children
        departments = []
        for yaml_office in yaml_data['departments']:
            num_new, modified = new_keywords(yaml_office, fr_keywords)
            if num_new:
                del fr_keywords[normalize_name(yaml_office['name'])]
                departments.append(modified)
                num_new_keywords += num_new
            else:
                departments.append(yaml_office)

        if num_new_keywords:
            yaml_data = dict(yaml_data, departments=departments)
            with open(filename, 'w') as f:
                f.write(yaml.dump(yaml_data, default_flow_style=False,
                                  allow_unicode=True))
                logging.info('Rewrote %s with %d new keywords', filename,
                             num_new_keywords)
    for name in fr_keywords:
        logging.warning('Could not find this agency: %s', name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    patch_yaml()
