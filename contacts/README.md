## Agency FOIA contact info

Downloading agency contact information for FOIA, from FOIA.gov.

`agencies.rb` hits the Ajax endpoints that the [FOIA.gov request form](http://www.foia.gov/report-makerequest.html) uses to load contact info, and downloads their HTML to the `html/` directory (ignored in git).

It then scrapes/parses the contact details out of them, and makes YAML files in the `data/` directory (versioned).

## Why do this?

The [FOIA.gov developer page](http://www.foia.gov/developer.html) has an [Excel spreadsheet](http://www.foia.gov/full-foia-contacts.xls) of contact info, but it is very incomplete.

This data is meant to be a starting point -- something that can be easily corrected, expanded, and repurposed.

## Using

Tested using Ruby `2.1.2`. Install dependencies with:

```bash
gem install curb nokogiri oj
```

Then run `agencies.rb` to download and parse everything.

If an agency's HTML has already been downloaded, it will not be downloaded again. To re-download, delete the `html/` directory and run again.

## Data

_**(Work-in-progress)**_

There are 99 agencies listed on FOIA.gov, and they each have 1 or more departments. Departments have addresses and phone numbers, and can also have fax numbers and email addresses.

They may have a website, or a request form, or both.

Data for an agency looks like this:

```json
{
  "abbreviation": "DoD",
  "name": "Department of Defense",
  "description": "The mission of the Department of Defense is...",
  "departments": [
    {
      "name": "Office of the Secretary and Joint Staff",
      "address": "FOIA Contact...",
      "phone": "(866) 574-4970",
      "fax": "(571) 372-0500",
      "email": null,
      "website": "http://www.dod.gov/pubs/foi/",
      "request_form": "http://www.dod.gov/pubs/foi/",
    }
  }
  ]
}
```

