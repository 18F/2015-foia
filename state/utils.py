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



# serialize and pretty print json
def json_for(object):
  return json.dumps(object, sort_keys=True, indent=2, default=format_datetime)

def format_datetime(obj):
  if isinstance(obj, datetime.datetime):
    return eastern_time_zone.localize(obj.replace(microsecond=0)).isoformat()
  elif isinstance(obj, datetime.date):
    return obj.isoformat()
  elif isinstance(obj, str):
    return obj
  else:
    return None

# mkdir -p, then write content
def write(content, destination, binary=False):
  mkdir_p(os.path.dirname(destination))

  if binary:
    mode = "bw"
  else:
    mode = "w"
  f = open(destination, mode)
  f.write(content)
  f.close()

# mkdir -p in python, from:
# http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as exc: # Python >2.5
    if exc.errno == errno.EEXIST:
      pass
    else:
      raise

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