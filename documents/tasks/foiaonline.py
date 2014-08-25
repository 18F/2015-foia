#!/usr/bin/env python

import sys
import os
import glob
import utils
import pdb
import json
import requests
import logging
import json
import re
from dateutil.parser import parse
from bs4 import BeautifulSoup

##
# This script assumes it's being run from one directory up,
#  as "./tasks/foiaonline.py".
#
# The basic strategy for downloading data is:
#
# 1. Run with --meta to page through search results for search
#    terms, and save unique IDs found during pagination.
# 2. Run bare to use any saved metadata from step 1 to download
#    more metadata, and download docs, for released FOIA records.
#
# You may find it helpful during development or archival to:
#
#  * Run with --resume to re-run or resume step 2, skipping over
#    records whose docs have already been downloaded.
#  * Run with --skip_doc to (re-)process metadata at any time, which
#    can be done purely from already-cached metadata from step 2.
##

##
# options for both meta and data:
#   debug: extra debug output
#   data: override data directory (defaults to "./data")
#
# options for --meta:
#   term: search term to paginate on
#   page: only do a particular page number
#   pages: go all the way up to page X (defaults to 1)
#     begin: combined with pages, starting page number (defaults to 1)
#
# options for data download:
#   skip_doc: don't actually download the doc, but write metadata
#             (this allows caching and reusing)
##

PER_PAGE = 100

# using an agency's acronym seems to reliably match all their results,
# and then of course others that have that slug in there somewhere.
#
# Side note: 'the' works, but appears to be a pretty bad search term overall.

AGENCIES = [
  "epa", # Environmental Protection Agency (~258,000)
  "cbp", # Customs and Border Protection (~120,000)
  "doc", # Department of Commerce (~25,000)
  "mspb", # Merit Systems Protection Board (~600)
  "flra", # Federal Labor Relations Authority (~300)
  "nara", # National Archives and Records Administration (~1,400)
  "pbgc", # Pension Benefit and Guaranty Corporation (~2,200)
  "don", # Department of the Navy (~23,000)
]

def run(options):
  if options.get("meta"):
    run_meta(options)
  else:
    run_data(options)


#### Data scraping

# no session needed for data, all objects have reliable permalinks
# for now: just `record` type objects
def run_data(options):
  # for now, default to records
  doc_type = options.get("type", "record")

  agency = options.get("agency")
  year = options.get("year")
  doc_id = options.get("id")

  if agency and year and doc_id:
    get_record(agency, year, doc_id, options)
  else:
    # e.g. data/foiaonline/data/record/EPA/2014/090004d2803333d6/

    if not doc_type: doc_type = "*"
    if not year: year = "*"

    # let people use lower-case slugs for agency on CLI
    if agency:
      agency = agency.upper()
    else:
      agency = "*"

    doc_paths = glob.glob(os.path.join(
      utils.data_dir(),
      "foiaonline/meta/%s/%s/%s/*" % (doc_type, agency, year))
    )
    doc_paths.sort()

    logging.warn("Going to fetch %i records." % len(doc_paths))

    for doc_path in doc_paths:
      pieces = doc_path.split("/")
      this_doc_type = pieces[-4]
      this_agency = pieces[-3]
      this_year = pieces[-2]
      this_doc_id = os.path.splitext(pieces[-1])[0]

      if this_doc_type == "record":
        get_record(this_agency, this_year, this_doc_id, options)


# given agency/year/ID to record metadata, scrape more metadata,
# download the document itself, extract text
# testing: 090004d2803333d6, epa, 2014
def get_record(agency, year, doc_id, options):

  meta_path = meta_path_for("record", agency, year, doc_id)
  json_path = data_path_for("record", agency, year, doc_id, "json")

  ## Special: resume mode
  #
  # since downloading documents requires re-downloading landing pages,
  # the only way to do a resumable mass download of docs is to
  # check for whether the doc has been downloaded yet. this, in turn,
  # requires checking for the presence of [doc_type].[file_type], and the
  # file_type needs to be loaded from [doc_type].json.
  #
  # So, if --resume is on, before re-downloading anything, check if we
  # have a parsed .json, and if so, load the file_type and check for
  # the doc itself. If present, return True and move on.
  if options.get("resume"):
    if os.path.exists(json_path):
      data = json.load(open(json_path))

      # it's an unreleased doc, move on anyway
      if data["unreleased"]:
        return True

      doc_path = data_path_for("record", agency, year, doc_id, data["file_type"])
      if os.path.exists(doc_path):
        logging.warn("[%s][%s][%s][%s] Skipping record, resuming..." % ("record", agency, year, doc_id))
        return True

  logging.warn("[%s][%s][%s][%s] Getting record..." % ("record", agency, year, doc_id))
  meta = json.load(open(meta_path))

  # download landing page for record
  url = "https://foiaonline.regulations.gov/foia/action/public/view/record?objectId=%s" % meta['id']

  # save the landing page no matter what, but only use it as a cache
  # if we're skipping the docs (download links are ephemeral :( )
  body = utils.download(url,
    cache_path_for("record", agency, year, doc_id),
    {'cache': options.get('skip_doc', False)}
  )

  # assume released
  unreleased = False

  doc = BeautifulSoup(body)
  main = doc.select("#mainForm")[0]

  # get some other metadata about the record
  headers = record_headers_from(doc)

  # now clear the labels so text can be more easily extracted
  for label in main.select("fieldset .formitem label"):
    label.extract()

  links = main.select("fieldset .formitem")

  # get the actual document download link/ID
  download_link = links[headers["title"]].select("a")
  if len(download_link) > 0:
    download_url = download_link[0]['href']
    download_url = "https://foiaonline.regulations.gov" + download_url

  # no link means it's not released
  else:
    unreleased = True

  title = links[headers["title"]].text.strip()
  author = links[headers["author"]].text.strip()
  if author == "N/A": author = None

  released_date = links[headers["released_on"]].text.strip()
  released_at = parse(released_date)
  released_on = released_at.strftime("%Y-%m-%d")

  request_id = links[headers["request"]].text.strip()

  file_type = links[headers["file_type"]].text.strip().lower()
  if file_type == "text": file_type = "txt"

  # this should correspond with it being unreleased
  if file_type.startswith("contact"):
    unreleased = True

  exemptions = links[headers["exemptions"]].text.strip()
  if exemptions == "N/A": exemptions = None
  retention = links[headers["retention"]].text.strip()
  if retention == "N/A": retention = None

  file_size = links[headers["file_size"]].text.strip()

  record = {
    "type": "record",
    "landing_id": doc_id,
    "landing_url": url,
    "agency": agency,
    "year": year,

    "request_id": request_id,
    "title": title,
    "released_on": released_on,
    "author": author,
    "exemptions": exemptions,
    "retention": retention
  }

  if unreleased:
    record["unreleased"] = True
  else:
    record["unreleased"] = False
    record["file_size"] = file_size
    record["file_type"] = file_type
    # ephemeral, used below to download, and kept for record-keeping
    record["download_url"] = download_url

  # 1) write JSON to disk at predictable path
  utils.write(utils.json_for(record), json_path)

  # 2) download the associated record doc (unless dry run)
  if unreleased:
    logging.warn("\tUnreleased doc, moving on.")
  elif options.get('skip_doc') is None:
    logging.warn("\tDownloading...")

    binary_types = ('pdf', 'doc', 'docx', 'xls', 'xlsx')
    doc_path = data_path_for("record", agency, year, doc_id, record['file_type'])

    result = utils.download(
      download_url,
      doc_path,
      {
        'binary': (record['file_type'].lower() in binary_types),
        'cache': not (options.get('force', False))
      }
    )

    # PDF extraction is easy enough
    if result and (record['file_type'] == 'pdf'):
      logging.warn("\tExtracting text from PDF...")
      utils.text_from_pdf(doc_path)


  return True

#### Metadata scraping

# session is needed to post the search form and page through metadata
def run_meta(options):

  term = options.get('term')
  if term is None:
    logging.warn("--term is required.")
    exit(1)

  session = new_session()

  # default to page 1
  start_page = options.get("begin", 1)

  # default to all pages, can limit
  if options.get("pages"):
    last_page = start_page + int(options.get("pages")) - 1
  else:
    # we'll figure out the last page from the first page
    last_page = None


  page = start_page
  while True:
    logging.warn("## Downloading page %i" % page)
    body = search(term, page, session)
    doc = BeautifulSoup(body)

    # if we're doing all pages, grab the last page number
    if last_page is None:
      last_page = last_page_for(doc)
      logging.warn("Last page: %s" % last_page)

    # actually save a page's worth of record and request #'s
    save_page(doc)

    if page >= last_page: break
    else: page += 1

    # failsafe in case of a while True gone mad
    if page > 100000: break


# returns an array of 100 dicts with tracking #, object ID, date, and type
def save_page(doc):
  headers = headers_from(doc)

  for row in doc.select("#dttPubSearch tbody tr"):
    id_td = row.select("td")[headers['tracking_number']]
    tracking = id_td.text.strip()

    object_link = id_td.select("a")[0]['href']
    object_id = re.search("objectId=([^&]+)", object_link).group(1)

    doc_type = row.select("td")[headers['type']].text.strip().lower()

    agency, year = split_id(tracking)

    result = {
      'id': object_id,
      'agency': agency,
      'year': year,
      'type': doc_type,
      'tracking': tracking
    }

    save_meta_result(result)

# save paged record/request metadata to
#   /data/foiaonline/meta/record/EPA/2014/EPA-R2-2014-SHSK4.json
#   /data/foiaonline/meta/request/EPA/2014/EPA-R2-APBNT2.json
def save_meta_result(result):
  path = meta_path_for(result['type'], result['agency'], result['year'], result['id'])

  # for paged metadata, don't overwrite if we've got it already,
  # we don't keep anything that should change.
  if os.path.exists(path):
    logging.debug("[%s][%s] Knew about it, skipping." % (result['id'], result['type']))
  else:
    logging.warn("[%s][%s] Newly discovered, saving metadata." % (result['id'], result['type']))
    utils.write(utils.json_for(result), path)

# get the agency and year from the ID,
# e.g. "EPA-R5-2013-001219" => "EPA", "2013"
#      "CBP-2014-038422"    => "CBP", "2014"
def split_id(id):
  agency = id.split("-")[0]
  year = re.search("-(\\d{4})-", id).group(1)
  return agency, year

# returns a mapping of header fields to order, to make this less brittle
# e.g. {'tracking_number' => 0, 'type' => 1}
def headers_from(doc):
  headers = {}
  fields = {
    "Tracking Number": "tracking_number",
    "Type": "type"
  }

  index = 0
  for link in doc.select("#dttPubSearch thead tr a"):
    text = link.text.strip()
    field = fields.get(text)
    if field:
      headers[field] = index
    index += 1

  return headers

def record_headers_from(doc):
  headers = {}
  main = doc.select("#mainForm")[0]

  index = 0
  for item in main.select("fieldset .formitem"):
    label = item.select("label")[0].text.strip().lower()
    if label.startswith("title"):
      headers["title"] = index
    elif label.startswith("request tracking"):
      headers["request"] = index
    elif label.startswith("author"):
      headers["author"] = index
    elif label.startswith("release date"):
      headers["released_on"] = index
    elif label.startswith("file format"):
      headers["file_type"] = index
    elif label.startswith("exemptions"):
      headers["exemptions"] = index
    elif label.startswith("retention"):
      headers["retention"] = index
    elif label.startswith("size"):
      headers["file_size"] = index
    elif label.startswith("ex."):
      pass # exemption 5 subtypes
    # TODO: discover more fields
    # else:
    #   raise Exception("Unexpected field on record details page: %s" % label)

    index += 1

  return headers

# calculate last page by finding total items, divide by per_page
def last_page_for(doc):
  text = doc.select(".subContentFull .subHeaderLeft")[0].text
  number = text.split(" ")[0]
  number = number.replace(",", "")

  total = int(number)
  remainder = ((total % PER_PAGE) > 0)
  last_page = int(total / PER_PAGE)
  if remainder:
    last_page += 1

  return last_page


# create a new FOIAonline session
def new_session():
  session = requests.Session()

  # GET the search form to establish session ID
  search_url = "https://foiaonline.regulations.gov/foia/action/public/search/"
  search_response = session.get(search_url)

  # and grab the two CSRF params from the contents
  search_doc = BeautifulSoup(search_response.content)
  session.__sourcePage = search_doc.select("input[name=_sourcePage]")[0]['value']
  session.__fp = search_doc.select("input[name=__fp]")[0]['value']

  return session

# given a session, return the raw HTML when searching for a term.
def search(term, page, session):

  base_url = "https://foiaonline.regulations.gov/foia/action/public/search//runSearch"

  # 100 requests or records matching the search, ordered by recently submitted
  post_params = {
    "searchParams.searchTerm": term,
    "searchParams.forRequest": "true",
    "searchParams.forRecord": "true",
    "searchParams.forAppeal": "true",
    "searchParams.forReferral": "true",
    "pageSize": PER_PAGE,
    "d-5509183-s": "submitted",
    "d-5509183-p": page,
    "_sourcePage": session.__sourcePage,
    "__fp": session.__fp
  }

  response = session.post(base_url, data=post_params)

  return bytes.decode(response.content)


##### Disk paths

def meta_path_for(doc_type, agency, year, doc_id):
  return os.path.join(utils.data_dir(),
    "foiaonline/meta",
    doc_type, agency, year,
    ("%s.json" % doc_id)
  )

# cache .html of landing pages for records/requests/etc
def cache_path_for(doc_type, agency, year, doc_id):
  return os.path.join(utils.data_dir(),
    "foiaonline/cache",
    doc_type, agency, year,
    ("%s.html" % doc_id)
  )

# save .json and .pdf docs (.txt's will end up there too)
def data_path_for(doc_type, agency, year, doc_id, extension):
  return os.path.join(utils.data_dir(),
    "foiaonline/data",
    doc_type, agency, year,
    ("%s/%s.%s" % (doc_id, doc_type, extension))
  )

run(utils.options()) if (__name__ == "__main__") else None
