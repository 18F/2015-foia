#!/usr/bin/env python

from itertools import takewhile
import logging
import os
from random import randint
import re
import sys
from urllib.parse import urlencode
from urllib.request import urlopen

from bs4 import BeautifulSoup
import yaml

import typos


# http://www.foia.gov/foiareport.js
# Excludes "ALL" (All agencies, though it's not, really).
# Excludes " ", which in `agenciesAb` is "SIGIR", the Special Inspector
# General for Iraq Reconstruction, which no longer accepts FOIA requests.
AGENCIES = [
    'USDA', 'DOC', 'DoD', 'ED', 'DOE', 'HHS', 'DHS', 'HUD', 'DOI', 'DOJ',
    'U.S. DOL', 'State', 'DOT', 'Treasury', 'VA', 'ACUS', 'USAID', 'ABMC',
    'NRPC', 'AFRH', 'BBG', 'CIA', 'CSB', 'USCCR', 'CPPBSD', 'CFTC', 'CFPB',
    'U.S. CPSC', 'CNCS', 'CIGIE', 'CSOSA', 'DNFSB', 'EPA', 'EEOC', 'CEQ',
    'OMB', 'ONDCP', 'OSTP', 'USTR', 'Ex-Im Bank', 'FCA', 'FCSIC', 'FCC',
    'FDIC', 'FEC', 'FERC', 'FFIEC', 'FHFA', 'FLRA', 'FMC', 'FMCS', 'FMSHRC',
    'FOMC', 'FRB', 'FRTIB', 'FTC', 'GSA', 'IMLS', 'IAF', 'LSC', 'MSPB', 'MCC',
    'NASA', 'NARA', 'NCPC', 'NCUA', 'NEA', 'NEH', 'NIGC', 'NLRB', 'NMB',
    'NSF', 'NTSB', 'USNRC', 'OSHRC', 'OGE', 'ONHIR', 'OPM', 'OSC', 'ODNI',
    'OPIC', 'PC', 'PBGC', 'PRC', 'RATB', 'US RRB', 'SEC', 'SSS', 'SBA', 'SSA',
    'SIGAR', 'STB', 'TVA', 'US ADF', 'CO', 'USIBWC', 'USITC', 'USPS', 'USTDA']

PHONE_RE = re.compile(
    r"""(?P<prefix>\+?[\d\s\(\)\-]*)"""
    r"""(?P<area_code>\(?\d{3}\)?[\s\-\(\)]*)"""
    r"""(?P<first_three>\d{3}[\-\s\(\)]*)"""
    r"""(?P<last_four>\d{4}[\-\s\(\)]*)"""
    r"""(?P<extension>[\s\(,]*?ext[ .]*?\d{3,5})?""", re.IGNORECASE)

ADDY_RE = re.compile('(?P<city>.*), (?P<state>[A-Z]{2}) (?P<zip>[0-9-]+)')


def agency_description(doc):
    """Account for BRs and such while finding the description."""
    description = ""
    after_h2 = doc("h2")[-1].next_elements
    next(after_h2)      # skip the text *within* the h2
    while_text = takewhile(lambda el: el.name is None or el.name == 'br',
                           after_h2)    # stop when we a different type
    for el in while_text:
        if el.name is None:
            description += el.string.strip()
        # Only want one new line when there are two BRs
        elif el.name == "br" and not description.endswith("\n"):
            description += "\n"
    return description.strip()


def clean_paragraphs(doc):
    """Find all paragraphs with content. Return paragraph els + content
    strings. Beautiful Soup doesn't handle unclosed tags very graciously, so
    account for paragraphs within paragraphs."""
    lines, ps = [], []
    for p in doc("p"):
        text = ""
        for child in p.contents:
            if child.name != 'p' and child.string and child.string.strip():
                text += child.string.strip()
        if text:
            lines.append(text)
            ps.append(p)
    return lines, ps


def clean_phone_number(line):
    """
    Given "(123) 456-7890 (Telephone)", extract the number and format
    """
    match = PHONE_RE.search(line)
    if match:
        # kill all non-numbers
        prefix = "".join(ch for ch in match.group("prefix") if ch.isdigit())
        area_code = "".join(ch for ch in match.group("area_code")
                            if ch.isdigit())
        first_three = "".join(ch for ch in match.group("first_three")
                              if ch.isdigit())
        last_four = "".join(ch for ch in match.group("last_four")
                            if ch.isdigit())
        number = "-".join([area_code, first_three, last_four])
        if prefix:
            number = "+" + prefix + " " + number
        extension = match.group("extension")
        if extension:
            extension = re.sub("\D", "", extension)
            number = number + " x" + extension
        return number

    else:
        raise Exception("Error extracting phone number",
                        "phone line: " + line)


def organize_address(address_list):
    """
    Converts a list containing address elements into a dictionary
    """
    address_dict = {}

    if len(address_list) > 1:
        address_dict['street'] = address_list[-2]
    if len(address_list) > 2:
        address_dict['address_lines'] = address_list[0:-2]

    match = ADDY_RE.match(address_list[-1])
    if match:
        address_dict['zip'] = match.group('zip')
        address_dict['state'] = match.group('state')
        address_dict['city'] = match.group('city')
    return address_dict


def split_address_from(lines):
    """Address goes until we find a phone or service center. Separate lines
    into address lines and remaining"""
    address_list, remaining = [], []
    cues = ("phone", "fax", "service center")
    for line in lines:
        if remaining:   # already switched over
            remaining.append(line)
        elif PHONE_RE.search(line) and any(q in line.lower() for q in cues):
            remaining.append(line)
        else:
            # Separate line breaks
            address_list.extend(re.split(r"[\n\r]+", line))
    if not remaining:
        raise Exception("error finding address end", lines)
    else:
        return address_list, remaining


def find_emails(lines, ps):
    """Find email address, then associated mailto"""
    email_re = re.compile(r"\be\-?mail", re.IGNORECASE)
    emails = []
    for idx, line in enumerate(lines):
        if email_re.search(line):
            a = ps[idx].a
            if a:
                emails_str = a["href"].replace("mailto:", "").strip()
                if "http://" not in emails_str:
                    emails.extend(re.split(r";\s*", emails_str))
            else:
                raise Exception("Error extracting email", line, idx,
                                ps[idx].prettify())
    return emails


def extract_numbers(phone_str):
    """
    Extracts all phone numbers from a line and adds them to a list
    """

    clean_numbers = []
    while True:
        if PHONE_RE.match(phone_str):
            clean_numbers.append(clean_phone_number(phone_str))
            if "," not in phone_str:
                break
            phone_str = PHONE_RE.sub(repl="", string=phone_str, count=1)
            phone_str = phone_str.replace(",", "", 1)
        else:
            break
    return clean_numbers


def organize_contact(value):
    """
    Organize contact info into a dictionary to facilitate extraction
    """
    value = value.split("Phone: ")
    name_str = value[0].strip(" ,'")
    phone_str = value[-1]
    clean_numbers = extract_numbers(phone_str)

    cleaned_value = {}
    if name_str:
        cleaned_value['name'] = name_str
    if clean_numbers:
        cleaned_value['phone'] = clean_numbers

    if cleaned_value:
        return cleaned_value


def find_bold_fields(ps):
    """Remaining fields: website, request form, anything else"""
    simple_search = ["service center", "public liaison", "notes",
                     "foia officer"]
    link_search = ["website", "request form"]
    for p in ps:
        strong = p.strong
        text = strong.string.replace(":", "").strip() if strong else ""
        lower = text.lower()
        if strong and text != "FOIA Contact":
            try:
                value = strong.next_sibling.string
            except:
                value = p.next_sibling.string
            if value:
                value = value.strip()
            yielded = False
            for term in simple_search:
                if term in lower:
                    yield term.replace(" ", "_"), value
                    yielded = True

            for term in link_search:
                if term in lower:
                    if p.a:
                        yield term.replace(" ", "_"), p.a["href"].strip()
                        yielded = True
                    else:
                        raise Exception("error extracting " + term,
                                        p.prettify())
            if not yielded:
                # FTC: FOIA Hotline
                # GSA: Program Manager
                yield "misc", (text, value)


def parse_department(elem, name):
    """Get data from a 'div' (elem) associated with a single department"""
    data = {"name": name, "top_level": False}
    lines, ps = clean_paragraphs(elem)
    # remove first el (which introduces the section)
    lines, ps = lines[1:], ps[1:]

    address_list, lines = split_address_from(lines)
    data['address'] = organize_address(address_list=address_list)

    ps = ps[-len(lines):]   # Also throw away associated paragraphs
    for line in lines:
        lower = line.lower()
        if ('phone' in lower and 'public liaison' not in lower
                and 'service center' not in lower and 'phone' not in data):
            data['phone'] = clean_phone_number(line)
        elif 'fax' in lower and 'fax' not in data:
            data['fax'] = clean_phone_number(line)
    emails = find_emails(lines, ps)
    if emails:
        data['emails'] = emails
    for key, value in find_bold_fields(ps):
        if key == 'misc':
            misc_key, misc_value = value
            if 'misc' not in data:
                data['misc'] = {}
            misc_value = organize_contact(misc_value)
            if misc_value:
                data['misc'][misc_key] = misc_value
        else:
            if key in ['service_center', 'public_liaison', 'foia_officer']:
                value = organize_contact(value)

            if value:
                data[key] = value
    return data


def parse_agency(abb, doc):
    """Make sense of a block of HTML from FOIA.gov"""
    agency_name = doc.h1.text.strip()
    description = agency_description(doc)

    # get each dept id and name, parse department from its div. Skip the first
    # as it is always a 'please select'
    departments = []
    for option in doc("option")[1:]:
        opt_id = option['value']
        elem = doc(id=opt_id)[0]
        # Needed to replace the ? with - in order to
        # accomate Carlsbad Field Office
        dept_name = option.string.strip().replace('?', '–')
        departments.append(parse_department(elem, dept_name))

    agency = {"abbreviation": abb,
              "name": agency_name,
              "description": description,
              "departments": departments}
    return agency


def fix_known_typos(text):
    """Account for faulty data"""
    for error, fix in typos.REPLACEMENTS.items():
        text = text.replace(error, fix)
    return text


def agency_yaml_filename(data_directory, agency_abbr):
    return os.path.join(data_directory, '%s.yaml' % agency_abbr)


def read_manual_data(agency_abbr, manual_data_dir='manual_data'):
    if os.path.isdir(manual_data_dir):
        filename = agency_yaml_filename(manual_data_dir, agency_abbr)
        if os.path.exists(filename):
            with open(filename, 'r') as yaml_file:
                manual_data = yaml.load(yaml_file)
            return manual_data


def update_list_in_dict(data, field, new_values_list):
    original_values = set(data.get(field, []))
    data[field] = sorted(list(original_values | set(new_values_list)))


def update_non_departments(agency_data, manual_data):
    """ Apply all the non-department changes from manual_data to agency_data.
    """

    agency_data = dict(agency_data)

    list_fields = ['common_requests', 'keywords']

    for field in manual_data.keys():
        if field not in list_fields + ['departments']:
            agency_data[field] = manual_data[field]

    for field in list_fields:
        if field in manual_data and field not in ['departments']:
            update_list_in_dict(agency_data, field, manual_data[field])
    return agency_data


def actual_apply(agency_data, manual_data):
    """ Actually apply the changes in manual_data to agency_data. This handles
    the departments. """

    agency_data = update_non_departments(agency_data, manual_data)
    manual_depts = {}
    if 'departments' in manual_data:
        for dept in manual_data['departments']:
            manual_depts[dept['name']] = dept

        departments = []
        if 'departments' in agency_data:
            for dept in agency_data['departments']:
                if dept['name'] in manual_depts:
                    new_department = update_non_departments(
                        dept, manual_depts[dept['name']])
                else:
                    new_department = dict(dept)
                departments.append(new_department)
            agency_data['departments'] = departments
    return agency_data


def apply_manual_data(agency_abbr, agency_data):
    """ In the manual data directory, we have all the manual over-rides for
    various contact fields. Apply those here. """
    manual_data = read_manual_data(agency_abbr)
    if manual_data:
        return actual_apply(agency_data, manual_data)
    else:
        return agency_data


def get_unknown_office_details(agency_data):
    for dept in agency_data['departments']:
        if dept['name'] == "I don't know which office":
            return dict(dept)


def all_but_unknown(agency_data):
    departments = [d for d in agency_data['departments']
                   if d['name'] != "I don't know which office"]
    return departments


def populate_parent(agency_data):
    unknown_office = get_unknown_office_details(agency_data)
    if unknown_office:
        departments = all_but_unknown(agency_data)
        agency_data = dict(agency_data, departments=departments)
        for field, value in unknown_office.items():
            if field not in ['name']:
                agency_data[field] = value
    return agency_data


def save_agency(abb):
    """For a given agency, download (if not already present) their HTML,
    process it, and save the resulting YAML"""
    os.makedirs('html', exist_ok=True)
    html_path = "html" + os.sep + "%s.html" % abb
    if not os.path.isfile(html_path):
        body = ""
        body = download_agency(abb)
        if body:
            with open(html_path, 'w') as f:
                f.write(body)
            logging.info("[%s] Downloaded.", abb)
        else:
            logging.warning("[%s] DID NOT DOWNLOAD, NO.", abb)
            return
    else:
        logging.info("[%s] Already downloaded.", abb)

    with open(html_path, 'r') as f:
        text = f.read()
    text = fix_known_typos(text)
    data = parse_agency(abb, BeautifulSoup(text))
    data = populate_parent(data)
    data = apply_manual_data(abb, data)
    save_agency_data(abb, data)


def save_agency_data(agency_abbr, data, data_directory='data'):
    """ Actually do the save. """
    os.makedirs(data_directory, exist_ok=True)

    if data:
        with open(data_directory + os.sep + "%s.yaml" % agency_abbr, 'w') as f:
            f.write(yaml.dump(data, default_flow_style=False,
                    allow_unicode=True))
            logging.info("[%s] Parsed.", agency_abbr)
    else:
        logging.warning("[%s] DID NOT PARSE, NO.", agency_abbr)


def save_agencies():
    """Save all agencies"""
    for agency in AGENCIES:
        save_agency(agency)


def agency_url(abb):
    """Construct download url, add cache busting -- the site does this too"""
    params = {"agency": abb, "Random": randint(1, 1000)}
    return "http://www.foia.gov/foia/FoiaMakeRequest?" + urlencode(params)


def download_agency(abb):
    """Agency HTML files"""
    url = agency_url(abb)
    return urlopen(url).read().decode("utf-8")


if __name__ == "__main__":
    """
        python scraper.py <<agency_abbreviation>>
        will only scrape and save the data for the provided agency.

        python scraper.py will scrape and save data for all the agencies.
    """
    logging.basicConfig(level=logging.INFO)

    agency_abbr = None
    if len(sys.argv) > 1:
        agency_abbr = sys.argv[1]

    if agency_abbr:
        save_agency(agency_abbr)
    else:
        save_agencies()
