#!/usr/bin/env python

import sys
import os
import utils
import json

# options:
#   page: only do a particular page number
#   pages: go all the way up to page X (defaults to 1)
#     begin: combined with pages, starting page number (defaults to 1)
#   per_page: how many to expect per_page (defaults to 200)
#   limit: only process X documents (regardless of pages)
#   dry_run: don't actually download the PDF, but write metadata
#   data: override data directory (defaults to "./data")

def run(options):
	pass


run(utils.options()) if (__name__ == "__main__") else None