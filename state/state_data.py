#!/usr/bin/env python

import sys

# Download everything from the Department of State's FOIA reading room.
# Iterate through each saved/serialized JSON page of search results, as
# downloaded from state_pages.js, downloading documents where linked.
#
# For each downloaded document, run it through `pdftotext -layout` to
# make a .txt file.

def run(options):
  pass


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