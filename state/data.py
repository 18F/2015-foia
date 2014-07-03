#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

# Download everything from the Department of State's FOIA reading room.
# Search for "*" and iterate through each JSON page of results, saving
# that page to disk. For each saved page, also extract individual documents

#

def run(options):



# given a page number and per_page, calculate the URL for State's JSON API
def url_for(page, per_page):
  offset = (page-1) * 200

  base = "http://foia.state.gov/searchapp/Search/SubmitSimpleQuery"
  # cache-buster
  base += "?_dc=%s" % str(int(time.time()))
  # boilerplate
  base += "&searchText=*&beginDate=&endDate=&collectionMatch=false&postedBeginDate=&postedEndDate=&caseNumber="
  # pagination
  base += "&page=%i&start=%i&limit=%i" % (page, offset, per_page)

  return base


# read options from the command line
#   e.g. ./state.py --since=2012-03-04 --debug
#     => {"since": "2012-03-04", "debug": True}
def options():
  options = {}
  for arg in sys.argv[1:]:
    if arg.startswith("--"):

      if "=" in arg:
        key, value = arg.split('=')
      else:
        key, value = arg, "True"

      key = key.split("--")[1]
      if value.lower() == 'true': value = True
      elif value.lower() == 'false': value = False
      options[key.lower()] = value
  return options

run(options())