## Agency FOIA contact info

Downloading agency contact information for FOIA, from FOIA.gov.

`contacts.rb` hits the Ajax endpoints that the [FOIA.gov request form](http://www.foia.gov/report-makerequest.html) uses to load contact info, and downloads their HTML to the `html/` directory (ignored in git).

It then scrapes/parses the contact details out of them, and makes YAML files in the `data/` directory (versioned).

## Why do this?

The [FOIA.gov developer page](http://www.foia.gov/developer.html) has an [Excel spreadsheet](http://www.foia.gov/full-foia-contacts.xls) of contact info, but it is very incomplete.

This data is meant to be a starting point -- something that can be easily corrected, expanded, and repurposed.

## Using

Tested using Ruby `2.1.2`. Install dependencies with:

```bash
gem install curb nokogiri htmlentities
```

Then run `contacts.rb` to download and parse everything.

If an agency's HTML has already been downloaded, it will not be downloaded again. To re-download, delete the `html/` directory and run again.

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

