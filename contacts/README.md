[![Coverage Status](https://coveralls.io/repos/18F/foia/badge.png)](https://coveralls.io/r/18F/foia)

## FOIA Contacts Data Builder

The scripts in this directory are used for constructing a FOIA contact dataset for Federal Agencies and Offices. The data collected are stored
in a set of yaml files inside the [data](https://github.com/18F/foia/tree/master/contacts/data) directory. These yaml files are
then uploaded to 18F's [Django application](https://github.com/18F/foia-hub).


## Process

Building the FOIA contacts database is a multi-step process:

1. Scraping the [FOIA.gov request form](https://www.foia.gov/report-makerequest.html) for contact data and adding in some additional manually curated data, stored in `manual_data/`.
2. Filling in missing data using a CSV rendition of an [Excel spreadsheet](https://www.foia.gov/full-foia-contacts.xls) hosted on FOIA.gov.
3. Downloading and adding descriptions, abbreviations, and IDs from the
[USA Contacts API](http://www.usa.gov/api/USAGovAPI/contacts.json/contacts)
4. Downloading and adding processing time data from [foia.gov/data](https://www.foia.gov/data.html)
5. Downloading keywords for agencies from the Federal Register.
6. Scraping agency and office FOIA websites to collect reading room urls.

## Running Scripts

First, install all of the Python dependencies:

```bash
pip install -r requirements.txt
```

Then run the following scripts in order:

```bash
python scraper.py
python layer_with_csv.py
# python layer_with_usa_contacts.py # USAGov contacts no longer supports this API
python processing_time_scraper.py
python keywords_from_fr.py
python layer_with_reading_room.py
```

## Clearing Cache

Many of the scripts cache the sites they are collecting data from
in order to facilitate rebuilding the contact data. Hence in order to collect
fresh data, certain files must be deleted. Below is each script cache:

```bash
scraper.py -> html/
layer_with_csv.py -> layering_data/full-foia-contacts.xls
layer_with_usa_contacts.py -> usa_contacts.sqlite
processing_time_scraper.py -> html/
keywords_from_fr.py -> fr.sqlite
```

## Script Details

### scraper.py

scraper.py collects contact data from [foia.gov's contacts pages](https://www.foia.gov/report-makerequest.html) and create the [data yaml files](https://github.com/18F/foia/tree/master/contacts/data) for each department. This script operates in two modes. Without any command line arguments it will
reprocess the data for all agencies. You can however provide an agency
abbreviation as a parameter, and it will only process the data for that agency.

Agency abbreviations are currently listed
[here.](https://github.com/18F/foia/blob/master/contacts/scraper.py#L21)

### layer_with_csv.py

layer_with_csv.py updates the [data yaml files](https://github.com/18F/foia/tree/master/contacts/data) with the [foia.gov's contacts spreadsheet](https://www.foia.gov/full-foia-contacts.xls).

### layer_with_usa_contacts.py

layer_with_usa_contacts.py collects data from the USA Contacts API](http://www.usa.gov/api/USAGovAPI/contacts.json/contacts) updates the yaml files with descriptions, abbreviations, and USA Contacts IDs.

### processing_time_scraper.py

processing_time_scraper.py crawls through request processing time reports
on foia.gov and updates the yaml files. Additionally, it creates
[request_time_data.csv](https://github.com/18F/foia/blob/master/contacts/request_time_data.csv), which contains all data available on request
processing times on foia.gov

### keywords_from_fr.py

keywords_from_fr.py updates the [data yaml files](https://github.com/18F/foia/tree/master/contacts/data) with keywords related to each agency's role from the [Federal Register](https://www.federalregister.gov/)

### layer_with_reading_room.py

layer_with_reading_room.py updates the [data yaml files](https://github.com/18F/foia/tree/master/contacts/data) with URLs for FOIA libraries and reading rooms scraped from each agency's FOIA page.

## Running the tests

Make sure you've installed the scraper's requirements, then run the tests
with:

```bash
nosetests
```

To run an individual test file, e.g. `tests/tests.py`:

```bash
python -m unittest discover -s tests -p tests.py
```

## Data

There are 99 agencies listed on FOIA.gov, and they each have 1 or more departments. Departments have addresses and phone numbers, and can also have fax numbers and email addresses.

Data for agencies and offices are organized on 2-tiered system like this:
```
agency_data (such as abbreviation, address, and common_requests)
departments:
  - office_data (such as address, name, etc.  )
  - office_data (such as address, name, etc.  )
  - office_data (such as address, name, etc.  )
agency_data (such as name, keywords, and request_time_stats )
```

Below is truncated example
```yaml
abbreviation: DOJ
departments:
- abbreviation: ATF
  address:
    address_lines:
    - Stephanie Boucher
    - Division Chief
    - Room 1E-400
    city: Washington
    state: DC
    street: 99 New York Avenue, NE
    zip: '20226'
  description: The Bureau of Alcohol, Tobacco, Firearms, and Explosives enforces federal
    criminal laws regulating the firearms and explosives industries.
  emails:
  - foiamail@atf.gov
  fax: 202-648-9619
  keywords:
  - Alcohol and alcoholic beverages
  - Arms and munitions
  - Arson
  - ...
  misc:
    Division Chief:
      name: Stephanie Boucher
      phone:
      - 202-648-8740
  name: Bureau of Alcohol, Tobacco, Firearms, and Explosives
  phone: 202-648-8740
  public_liaison:
    name: Stephanie Boucher
    phone:
    - 202-648-8740
  request_time_stats:
    '2013':
      complex_average_days: '50.05'
      complex_highest_days: '600'
      complex_lowest_days: less than 1
      complex_median_days: '28'
      expedited_processing_average_days: '95'
      expedited_processing_highest_days: '95'
      expedited_processing_lowest_days: '95'
      expedited_processing_median_days: '95'
  service_center:
    phone:
    - 202-648-8740
  top_level: true
  usa_id: '49081'
  website: http://www.atf.gov/content/contact-us/FOIA
description: The Department of Justice works to enforce federal law, to seek just
  punishment for the guilty, and to ensure the fair and impartial administration of
  justice.
emails:
- MRUFOIA.Requests@usdoj.gov
fax: 301-341-0772
keywords:
- Accounting
- Administrative practice and procedure
- ...
name: Department of Justice
phone: 301-583-7354
public_liaison:
  phone:
  - 301-583-7354
request_time_stats:
  '2013':
    complex_average_days: '115.81'
    complex_highest_days: '1232'
    complex_lowest_days: less than 1
    complex_median_days: '64'
    expedited_processing_average_days: '142.91'
    expedited_processing_highest_days: '997'
    expedited_processing_lowest_days: less than 1
    expedited_processing_median_days: '30.5'
    simple_average_days: '21.75'
    simple_highest_days: '815'
    simple_lowest_days: less than 1
    simple_median_days: '12'
service_center:
  phone:
  - 301-583-7354
top_level: false
usa_id: '52686'
```
