import datetime
import urllib.parse
import os, os.path, errno, sys, traceback, subprocess
import re, html.entities
import json
from bs4 import BeautifulSoup


# scraper should be instantiated at class-load time, so that it can rate limit appropriately
import scrapelib
scraper = scrapelib.Scraper(requests_per_minute=60, follow_robots=False, retry_attempts=3)
scraper.user_agent = "18f/foia (https://github.com/18f/foia/pull/11)"




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