#!/usr/bin/env python

import sys
import os
import utils
import requests
import json
from bs4 import BeautifulSoup

# options:
#   page: only do a particular page number
#   pages: go all the way up to page X (defaults to 1)
#     begin: combined with pages, starting page number (defaults to 1)
#   per_page: how many to expect per_page (defaults to 200)
#   limit: only process X documents (regardless of pages)
#   dry_run: don't actually download the PDF, but write metadata
#   data: override data directory (defaults to "./data")

def run(options):

  session = new_session()
  print(search("the", session))


# will initialize a requests session, and stick some hidden params onto it
def new_session():
  session = requests.Session()
  # first, GET the search form to fetch the _sourcePage CSRF param
  search_url = "https://foiaonline.regulations.gov/foia/action/public/search/"
  search_response = session.get(search_url)

  search_doc = BeautifulSoup(search_response.content)
  session.__sourcePage = search_doc.select("input[name=_sourcePage]")[0]['value']
  session.__fp = search_doc.select("input[name=__fp]")[0]['value']

  return session

# given a session, return the raw HTML when searching for a term.
def search(term, session):

  base_url = "https://foiaonline.regulations.gov/foia/action/public/search//runSearch"

  post_params = {
    "searchParams.searchTerm": term,
    "searchParams.forRequest": "true",
    "searchParams.forAppeal": "true",
    "searchParams.forRecord": "true",
    "_sourcePage": session.__sourcePage,
    "__fp": session.__fp
  }

  response = session.post(base_url, data=post_params)

  return response.content


run(utils.options()) if (__name__ == "__main__") else None
