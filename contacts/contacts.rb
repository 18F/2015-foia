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
require 'yaml'
require 'rubygems'

require 'curl'
require 'nokogiri'
require 'htmlentities'

FileUtils.mkdir_p "html"
FileUtils.mkdir_p "data"

# Transformed from the `agenciesFile` array at http://www.foia.gov/foiareport.js
#
# Excludes "ALL" (All agencies, though it's not, really).
# Excludes " ", which in `agenciesAb` is "SIGIR", the Special Inspector
# General for Iraq Reconstruction, which no longer accepts FOIA requests.
AGENCIES = ['USDA', 'DOC', 'DoD', 'ED', 'DOE', 'HHS', 'DHS', 'HUD', 'DOI', 'DOJ', 'U.S. DOL', 'State', 'DOT', 'Treasury', 'VA', 'ACUS', 'USAID', 'ABMC', 'NRPC', 'AFRH', 'BBG', 'CIA', 'CSB', 'USCCR', 'CPPBSD', 'CFTC', 'CFPB', 'U.S. CPSC', 'CNCS', 'CIGIE', 'CSOSA', 'DNFSB', 'EPA', 'EEOC', 'CEQ', 'OMB', 'ONDCP', 'OSTP', 'USTR', 'Ex-Im Bank', 'FCA', 'FCSIC', 'FCC', 'FDIC', 'FEC', 'FERC', 'FFIEC', 'FHFA', 'FLRA', 'FMC', 'FMCS', 'FMSHRC', 'FOMC', 'FRB', 'FRTIB', 'FTC', 'GSA', 'IMLS', 'IAF', 'LSC', 'MSPB', 'MCC', 'NASA', 'NARA', 'NCPC', 'NCUA', 'NEA', 'NEH', 'NIGC', 'NLRB', 'NMB', 'NSF', 'NTSB', 'USNRC', 'OSHRC', 'OGE', 'ONHIR', 'OPM', 'OSC', 'ODNI', 'OPIC', 'PC', 'PBGC', 'PRC', 'RATB', 'US RRB', 'SEC', 'SSS', 'SBA', 'SSA', 'SIGAR', 'STB', 'TVA', 'US ADF', 'CO', 'USIBWC', 'USITC', 'USPS', 'USTDA']

# regex for phones as they appear here
PHONE = /\+?[\d\s\(\)\-]*(\(?\d{3}\)?[\s\-\(\)]*\d{3}[\-\s\(\)]*\d{4})/i

# parsing workhorse functions: making sense of a block of HTML from FOIA.gov
def parse_agency(abb, html_path)
  html = File.read html_path
  doc = Nokogiri::HTML html

  name = doc.at("h1").text.strip
  description = (doc / :h2).last.next_sibling.text.strip

  # get each dept id and name, parse department from its div
  departments = doc.css("option")[1..-1].map do |option|
    id = option['value']
    elem = doc.css("div##{id}").first
    name = option.text.strip
    parse_department elem, name
  end

  {
    "abbreviation" => abb,
    "name" => name,
    "description" => description,
    "departments" => departments
  }
end

# get data from a 'div'for that department, and the name
def parse_department(elem, name)
  data = {
    "name" => name
  }

  # clean up each line, ignore the first one
  lines = []
  ps = []
  (elem / :p)[1..-1].each do |p|
    text = p.text.strip
    text = HTMLEntities.new.decode text
    text = text.gsub /\n\s+/, " "

    # remove empty lines, including unicode/nbsp spaces
    if text.gsub(/[[:space:]]/, '').strip != ""
      lines << text
      ps << p
    end
  end

  # first, get address - starts with line 2, then goes until we find a
  # phone or service center. So find that first.
  non_address = -1
  so_far = 0
  lines.each_with_index do |line, i|
    if (so_far >= 2) and (((line =~ PHONE) and (line =~ /phone|fax/i)) or (line =~ /Service Center/i))
      non_address = i
      break
    end
    so_far += 1
  end

  if non_address < 0
    puts "name: #{name}"
    puts "== ERROR FINDING ADDRESS END. =="
    exit
  else
    data['address'] = lines[0...non_address].map {|line| line.split(/[\n\r]+/)}.flatten
  end

  if phone = lines.select {|l| l =~ /phone/i}.first
    if (phone !~ /public liaison/i) and (phone !~ /service center/)
      data['phone'] = extract_phone(phone)
    end
  end

  if fax = lines.select {|l| l =~ /\bfax/i}.first

    if fax == "(256) 544-007 (Fax)"
      fax = "(256) 544-0007" # fix, see http://foia.msfc.nasa.gov/reading.html
    end

    data['fax'] = extract_phone(fax)
  end

  # find email address, match to original p
  lines.each_with_index do |line, i|
    if line =~ /\be\-?mail/i
      if a = ps[i].at("a")
        emails = a['href'].sub("mailto:", "").strip
        if emails !~ /http:\/\//
          data['emails'] = emails.split(/;\s+/)
        end
      else
        puts line
        puts i
        puts ps[i].to_html
        puts " == ERROR EXTRACTING EMAIL. =="
        exit
      end
      break
    end
  end

  # remaining fields: website, request form, anything else
  ps.each do |p|
    next unless strong = p.at("strong")
    text = strong.text.tr(":", "").strip
    next if text == "FOIA Contact"

    if text.downcase == "website"
      if a = p.at("a")
        data['website'] = a['href'].strip
      else
        puts p
        puts "== ERROR EXTRACTING WEBSITE. =="
        exit
      end
    elsif text.downcase =~ /request form/i
      if a = p.at("a")
        data['request_form'] = a['href'].strip
      else
        puts p
        puts "== ERROR EXTRACTING WEBSITE. =="
        exit
      end
    else
      # data['misc'] ||= []
      # data['misc'][key] = strong.next_sibling.text.strip
    end

  end

  data
end

# given "(202) 345-6789 (Telephone)", extract the number
def extract_phone(line)
  if match = line.match(PHONE)
    number = match[0]
    number = number.gsub /[^\d]/, '' # kill all non-numbers

    if number.size > 10
      prefix = number[0...(number.size - 10)]
      number = number[(number.size-10)..-1]
    else
      prefix = nil
    end

    number = [number[0..2], number[3..5], number[6..9]].join "-"
    prefix ? "+#{prefix} #{number}" : number
  else
    puts "phone line: #{line}"
    puts "== ERROR EXTRACTING PHONE NUMBER. =="
    exit
  end
end

# download and output stuff

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

  data = parse_agency abb, html_path
  if data
    File.open("data/#{abb}.yaml", "w") {|f| f.write YAML.dump(data)}
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