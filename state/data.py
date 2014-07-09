#!/usr/bin/env python

import sys
import os
import utils
import json

FIELDS = ('subject', 'documentClass', 'pdfLink', 'originalLink',
  'docDate', 'postedDate', 'from', 'to', 'messageNumber', 'caseNumber')

# Download everything from the Department of State's FOIA reading room.
# Iterate through each saved/serialized JSON page of search results, as
# downloaded from state_pages.js, downloading documents where linked.
#
# For each downloaded document, run it through `pdftotext -layout` to
# make a .txt file. (pdftotext is required)

# options:
#   page: only do a particular page number
#   pages: do this many pages (defaults to 1)
#   per_page: how many to expect per_page (defaults to 200)
#
#   TODO:
#   dry_run: don't actually download the PDF, but write metadata

# when paginated with 200 per-page

def run(options):
  pages = []
  if options.get('page'):
    pages = [int(options.get('page'))]
  elif options.get('pages'):
    pages = list(range(1, int(options.get('pages'))+1))
  else:
    pages = [1]

  per_page = int(options.get('per_page', 200))

  print("Processing pages %i through %i." % (pages[0], pages[-1]))

  # go through each requested page
  for page in pages:
    print("[%i] Loading page." % page)
    page_path = "pages/%i/%i.json" % (per_page, page)
    page_data = json.load(open(page_path))
    for result in page_data['Results']:
      do_document(result, page, options)



# passed in each Result from a page of data
def do_document(result, page, options):
  if result.get('pdfLink') is None:
    print("\tERROR, no pdfLink for document.")
    return False

  document = clean_document(result)

  # 1) write JSON to disk at predictable path
  json_path = path_for(page, document['document_id'], "json")
  utils.write(utils.json_for(document), json_path)

  # 2) download pdfLink (unless dry run)
  # 2a) save to disk next to JSON as document.pdf
  # 2b) extract text from pdfLink, save to disk as document.txt

  return True

# clean up a document's details from a raw result.
# turn 0001 dates into null, empty strings into null, etc.
def clean_document(result):
  document = {}
  for field in FIELDS:
    value = result.get(field)
    if (value is None) or (value.strip() == "") or (value.strip() == "n/a"):
      document[field] = None
    else:
      document[field] = value

  # this means no date
  if document['docDate'].startswith("0001"):
    document['docDate'] = None

  # standardize on forward slashes
  document['pdfLink'] = document['pdfLink'].replace("\\", "/")

  # inferred fields: url, file name, extension, and unique ID
  document['url'] = url_for(document['pdfLink'])
  document['filename'] = os.path.basename(document['pdfLink'])
  document['file_type'] = os.path.splitext(document['filename'])[1]
  document['document_id'] = document_id_for(result['pdfLink'])

  return document


# make a unique ID out of the document's URL path
# cause that's all we really got for unique IDs here
# examples:
#   "DOCUMENTS\\IntAgreements\\0000CD01.pdf"
#   "DOCUMENTS/5-FY2014/F-2011-03391/DOC_0C17693711/C17693711.pdf"
#
# should yield something like "DOCUMENTS-IntAgreements-0000CD01"
def document_id_for(original_path):
  name, ext = os.path.splitext(original_path)
  return name.replace("/", "-")

# figure out the URL that a filename should generate
# examples:
#   "DOCUMENTS\\IntAgreements\\0000CD01.pdf"
#   "DOCUMENTS/5-FY2014/F-2011-03391/DOC_0C17693711/C17693711.pdf"
def url_for(original_path):
  return "http://foia.state.gov/searchapp/" + original_path

# where to write data to disk
def path_for(page, document_id, ext):
  return "data/%i/%s/document.%s" % (page, document_id, ext)

run(utils.options())