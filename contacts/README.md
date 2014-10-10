## Agency FOIA contact info

Downloading agency contact information for FOIA, from FOIA.gov.

This is a two step process, first hitting the [FOIA.gov request form](http://www.foia.gov/report-makerequest.html) and then filling in missing
data using an [Excel spreadsheet](http://www.foia.gov/full-foia-contacts.xls).

It scrapes/parses the contact details out of these sources, and makes YAML files in the `data/` directory (versioned).

## Using

First, install all of the Python dependencies (we assume you are familiar with
Python environments, pip and the like). Then run the three relevant scripts:

```bash
pip install -r requirements.txt
python scraper.py
python layer_with_csv.py
python keywords_from_fr.py
```

If an agency's HTML has already been downloaded, it will not be downloaded
again. To re-download, delete the `html/` directory and run again. Similarly,
the XLS file is stored locally in the `xls/` directory. JSON responses pulled
from the Federal Register for keywords are logged in an SQLite DB.

## Data

_**(Work-in-progress)**_

There are 99 agencies listed on FOIA.gov, and they each have 1 or more departments. Departments have addresses and phone numbers, and can also have fax numbers and email addresses.

They may have a website, or a request form, or both.

Data for an agency looks like this:

```yaml
---
abbreviation: GSA
name: Headquarters
description: GSA's mission is to use expertise to provide innovative solutions for
  our customers in support of their missions and by so doing, foster an effective,
  sustainable, and transparent government for the American people.
departments:
- name: Headquarters
  address:
  - FOIA Contact
  - FOIA Requester Service Center (H1C)
  - Room 7308
  - 1800 F. Street, NW
  - Washington, DC 20405
  phone: 855-675-3642
  fax: 202-501-2727
  emails:
  - gsa.foia@gsa.gov
  service_center: 'Phone: (855) 675-3642'
  misc:
    Program Manager: 'Travis Lewis, Phone: (202) 219-3078'
  public_liaison: 'Audrey Corbett Brooks, Phone: (202) 205-5912'
  website: http://www.gsa.gov/portal/category/21416

```

### Running the tests

Make sure you've installed the scraper's requirements, then run the tests
with:

```bash
nosetests
```
