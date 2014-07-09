#!/usr/bin/env node

/*

Download pages from the undocumented JSON-like API that the
State Department's FOIA virtual library uses to power its search
results. Pages are actually JavaScript, not JSON, so `eval()` is
used to evaluate results and then serialize proper JSON.

Actual contents of these pages are processed and used to download
content in state_data.py.

*/

var request = require("request");
var argv = require('minimist')(process.argv.slice(2));
var async = require('async');
var fs = require('fs');

// as of 2014-07-02, total hits are 92054
var total = 92054;
// total pages under a 200-per-page regime: 461

var run = function() {

  var pages = argv.pages || 1;
  var per_page = argv.per_page || 200;

  // async wants to iterate over an array of arguments, so, okay
  var all_pages = []; // 1 to N
  for (var i=1; i<=pages; i++)
    all_pages.push({page: i, per_page: per_page});


  async.eachSeries(all_pages, downloadPage, function(err) {
    if (err) console.log("Error doing things!!");

    console.log("All done. Saved " + pages + " pages to disk.");
    process.exit(0);
  });
};

// download a given page, with the given pagination details
var downloadPage = function(details, done) {

  var url = urlFor(details.page, details.per_page);
  console.log("Fetching page " + details.page + "\n");

  var destination = destFor(details.page, details.per_page);

  request(url, function(err, response, body) {
    if (err) {
      console.log("Error!");
      return done();
    }

    var parsed = {};
    eval("parsed = " + body + ";");
    // console.dir(parsed);

    fs.writeFileSync(destination, JSON.stringify(parsed, undefined, 2));

    done();
  })
};

// a folder of JSON for pages, gathered by page size
var destFor = function(page, per_page) {
  return "pages/" + per_page + "/" + page + ".json";
}

var urlFor = function(page, per_page) {
  var offset = (page-1) * 200;

  var base = "http://foia.state.gov/searchapp/Search/SubmitSimpleQuery";
  // cache-buster
  base += "?_dc=" + (new Date()).getTime();
  // boilerplate
  base += "&searchText=*&beginDate=&endDate=&collectionMatch=false&postedBeginDate=&postedEndDate=&caseNumber="
  // pagination
  base += "&page=" + page + "&start=" + offset + "&limit=" + per_page;

  return base
}


run();