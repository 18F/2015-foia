#!/usr/bin/env node

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


  var url = urlFor(page, per_page);
  console.log(url + "\n");

  request(url, function(err, response, body) {
    if (err) return console.log("Error!");

    console.log("Success");
    var parsed = {};
    eval("parsed = " + body + ";");
    console.dir(parsed);
  })

};

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