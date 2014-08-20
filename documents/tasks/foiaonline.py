#!/usr/bin/env python

import sys
import os
import utils
import pdb
import requests
import logging
import json
import re
from dateutil.parser import parse
from bs4 import BeautifulSoup

# options:
#   page: only do a particular page number
#   pages: go all the way up to page X (defaults to 1)
#     begin: combined with pages, starting page number (defaults to 1)
#   per_page: how many to expect per_page (defaults to 200)
#   limit: only process X documents (regardless of pages)
#   dry_run: don't actually download the PDF, but write metadata
#   data: override data directory (defaults to "./data")

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
    doc_id = id_td.text.strip()

    object_link = id_td.select("a")[0]['href']
    object_id = re.search("objectId=([^&]+)", object_link).group(1)

    doc_type = row.select("td")[headers['type']].text.strip().lower()

    agency, year = split_id(doc_id)

    result = {
      'id': doc_id,
      'agency': agency,
      'year': year,
      'type': doc_type,
      'object_id': object_id
    }

    save_meta_result(result)

# save paged record/request metadata to
#   /data/foiaonline/meta/record/EPA/2014/EPA-R2-2014-SHSK4.json
#   /data/foiaonline/meta/request/EPA/2014/EPA-R2-APBNT2.json
def save_meta_result(result):

  path = os.path.join(utils.data_dir(),
    "foiaonline/meta",
    result['type'], result['agency'], result['year'],
    "%s.json" % (result['id'])
  )

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
# e.g. {'tracking' => 0, 'object_id' => 1}
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


run(utils.options()) if (__name__ == "__main__") else None
