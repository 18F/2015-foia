#!/usr/bin/env ruby

# Hits the Ajax endpoints that http://www.foia.gov/report-makerequest.html
# uses to load contact info, and scrapes the contact details out of them.
#
# At http://www.foia.gov/developer.html, there is a spreadsheet of contact info:
# http://www.foia.gov/full-foia-contacts.xls
#
# But this spreadsheet is very incomplete.

# Gem dependencies:
#  curb
#  nokogiri

require 'cgi'
require 'fileutils'
require 'rubygems'

require 'curl'
require 'nokogiri'
require 'oj'

FileUtils.mkdir_p "html"
FileUtils.mkdir_p "data"

# Transformed from the `agenciesFile` array at http://www.foia.gov/foiareport.js
#
# Excludes "ALL" (All agencies, though it's not, really).
# Excludes " ", which in `agenciesAb` is "SIGIR", the Special Inspector
# General for Iraq Reconstruction, which no longer accepts FOIA requests.
AGENCIES = ['USDA', 'DOC', 'DoD', 'ED', 'DOE', 'HHS', 'DHS', 'HUD', 'DOI', 'DOJ', 'U.S. DOL', 'State', 'DOT', 'Treasury', 'VA', 'ACUS', 'USAID', 'ABMC', 'NRPC', 'AFRH', 'BBG', 'CIA', 'CSB', 'USCCR', 'CPPBSD', 'CFTC', 'CFPB', 'U.S. CPSC', 'CNCS', 'CIGIE', 'CSOSA', 'DNFSB', 'EPA', 'EEOC', 'CEQ', 'OMB', 'ONDCP', 'OSTP', 'USTR', 'Ex-Im Bank', 'FCA', 'FCSIC', 'FCC', 'FDIC', 'FEC', 'FERC', 'FFIEC', 'FHFA', 'FLRA', 'FMC', 'FMCS', 'FMSHRC', 'FOMC', 'FRB', 'FRTIB', 'FTC', 'GSA', 'IMLS', 'IAF', 'LSC', 'MSPB', 'MCC', 'NASA', 'NARA', 'NCPC', 'NCUA', 'NEA', 'NEH', 'NIGC', 'NLRB', 'NMB', 'NSF', 'NTSB', 'USNRC', 'OSHRC', 'OGE', 'ONHIR', 'OPM', 'OSC', 'ODNI', 'OPIC', 'PC', 'PBGC', 'PRC', 'RATB', 'US RRB', 'SEC', 'SSS', 'SBA', 'SSA', 'SIGAR', 'STB', 'TVA', 'US ADF', 'CO', 'USIBWC', 'USITC', 'USPS', 'USTDA']

# the workhorse: how to parse a block of HTML from FOIA.gov
def parse_agency(abb)
  # TBD
  {}
end

def agency_url(abb)
  # cache bust, the site does this too
  random = rand 50
  "http://www.foia.gov/foia/FoiaMakeRequest?agency=#{CGI.escape abb}&Random=#{random}"
end

def download_agency(abb)
  url = agency_url abb
  response = Curl.get url
  response.body
end

def save_agency(abb)
  html_path = "html/#{abb}.html"
  if !File.exist?(html_path)
    body = download_agency abb
    if body
      File.open(html_path, "w") {|f| f.write body}
      puts "[#{abb}] Downloaded."
    else
      puts "[#{abb}] DID NOT DOWNLOAD, NO."
      return
    end
  else
    puts "[#{abb}] Already downloaded."
  end

  data = parse_agency abb
  if data
    File.open("data/#{abb}.json", "w") {|f| f.write Oj.dump(data)}
    puts "[#{abb}] Parsed."
  else
    puts "[#{abb}] DID NOT PARSE, NO."
    return
  end
end

def save_agencies
  AGENCIES.each {|abb| save_agency abb}
end

# `./agencies.rb` does everything.
# `./agencies.rb AGENCY` does just one agency.
if __FILE__ == $0
  if ARGV[0] and (ARGV[0].strip != "")
    save_agency ARGV[0]
  else
    save_agencies
  end
end