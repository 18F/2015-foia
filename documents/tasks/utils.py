import datetime
import urllib.parse
import os, os.path, errno, sys, traceback, subprocess
import re, html.entities
import traceback
import json
import logging
from bs4 import BeautifulSoup


# scraper should be instantiated at class-load time, so that it can rate limit appropriately
import scrapelib
scraper = scrapelib.Scraper(requests_per_minute=30, retry_attempts=3)
scraper.user_agent = "18F (https://18f.gsa.gov, https://github.com/18f/foia)"


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

# download the data at url
def download(url, destination=None, options=None):
  options = {} if not options else options
  cache = options.get('cache', True) # default to caching
  binary = options.get('binary', False) # default to assuming text

  # check cache first
  if destination and cache and os.path.exists(destination):
    logging.info("## Cached: (%s, %s)" % (destination, url))

    # if a binary file is cached, we're done
    if binary:
      return True

    # otherwise, decode it for return
    with open(destination, 'r', encoding='utf-8') as f:
      body = f.read()

  # otherwise, download from the web
  else:
    logging.info("## Downloading: %s" % url)
    if binary:
      if destination:
        logging.info("## \tto: %s" % destination)
      else:
        raise Exception("A destination path is required for downloading a binary file")
      try:
        mkdir_p(os.path.dirname(destination))
        scraper.urlretrieve(url, destination)
      except scrapelib.HTTPError as e:
        # intentionally print instead of using logging,
        # so that all 404s get printed at the end of the log
        print("Error downloading %s:\n\n%s" % (url, format_exception(e)))
        return None
    else: # text
      try:
        if destination: logging.info("## \tto: %s" % destination)
        response = scraper.urlopen(url)
      except scrapelib.HTTPError as e:
        # intentionally print instead of using logging,
        # so that all 404s get printed at the end of the log
        print("Error downloading %s:\n\n%s" % (url, format_exception(e)))
        return None

      body = response
      if not isinstance(body, str): raise ValueError("Content not decoded.")

      # don't allow 0-byte files
      if (not body) or (not body.strip()):
        return None

      # cache content to disk
      if destination:
        write(body, destination, binary=binary)

  # don't return binary content
  if binary:
    return True
  else:
    # whether from disk or web, unescape HTML entities
    return unescape(body)

# taken from http://effbot.org/zone/re-sub.htm#unescape-html
def unescape(text):

  def remove_unicode_control(str):
    remove_re = re.compile('[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]')
    return remove_re.sub('', str)

  def fixup(m):
    text = m.group(0)
    if text[:2] == "&#":
      # character reference
      try:
        if text[:3] == "&#x":
          return chr(int(text[3:-1], 16))
        else:
          return chr(int(text[2:-1]))
      except ValueError:
        pass
    else:
      # named entity
      try:
        text = chr(html.entities.name2codepoint[text[1:-1]])
      except KeyError:
        pass
    return text # leave as is

  text = re.sub("&#?\w+;", fixup, text)
  text = remove_unicode_control(text)
  return text

# uses pdftotext to get text out of PDFs.
def text_from_pdf(pdf_path):
  try:
    subprocess.Popen(["pdftotext", "-v"], shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
  except FileNotFoundError:
    logging.warn("Install pdftotext to extract text! The pdftotext executable must be in a directory that is in your PATH environment variable.")
    return None

  text_path = "%s.txt" % os.path.splitext(pdf_path)[0]

  try:
    subprocess.check_call("pdftotext -layout \"%s\" \"%s\"" % (pdf_path, text_path), shell=True)
  except subprocess.CalledProcessError as exc:
    logging.warn("Error extracting text to %s:\n\n%s" % (text_path, format_exception(exc)))
    return None

  if os.path.exists(text_path):
    return text_path
  else:
    logging.warn("Text not extracted to %s" % text_path)
    return None

def format_exception(exception):
  exc_type, exc_value, exc_traceback = sys.exc_info()
  return "\n".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

def data_dir():
  params = options()
  if params.get("data"):
    return params.get("data")
  else:
    return "data"

# logging level
if options().get("debug"):
  logging.basicConfig(format='%(message)s', level='DEBUG')