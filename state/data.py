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





# make a unique ID out of the document's URL path
# cause that's all we really got for unique IDs here
# examples:
#   "DOCUMENTS\\IntAgreements\\0000CD01.pdf"
#   "DOCUMENTS/5-FY2014/F-2011-03391/DOC_0C17693711/C17693711.pdf"
#
# should yield something like "DOCUMENTS-IntAgreements-0000CD01"
def document_id_for(filename):
  original_path = original_path.replace("\\", "/")
  name, ext = os.path.splitext(original_path)[0]
  return name.replace("/", "-")

# figure out the URL that a filename should generate
# examples:
#   "DOCUMENTS\\IntAgreements\\0000CD01.pdf"
#   "DOCUMENTS/5-FY2014/F-2011-03391/DOC_0C17693711/C17693711.pdf"
def url_for(original_path):
  return "http://foia.state.gov/searchapp/" + original_path.replace("\\", "/")

run(options())