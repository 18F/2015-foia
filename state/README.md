### State Department Virtual Reading Room

This is a scraper for the metadata, downloaded contents, and extracted text from [State's FOIA Library Search page](http://foia.state.gov/Search/results.aspx?searchText=*&beginDate=&endDate=&publishedBeginDate=&publishedEndDate=&caseNumber=). There are ~92,000 documents there, published in quarterly batches.

It's broken into two scripts:

* a Node scraper that downloads the initial "pages" of metadata using an undocumented API. It's in Node because the JSON is actually JavaScript, which Node can easily just `eval()` into an actual JS object, and then serialize to real JSON.
* A Python scraper that runs over each page and download the linked-to docs, and extract text (using `pdftotext`).

### Downloading pages of metadata

The Node scraper, `pages.js`, downloads pages (defaults to 200 at a time) of FOIA search results ([example](http://foia.state.gov/searchapp/Search/SubmitSimpleQuery?_dc=1404140029362&searchText=*&beginDate=&endDate=&collectionMatch=false&postedBeginDate=&postedEndDate=&caseNumber=&page=1&start=20&limit=20)), then runs `eval()` on them and saves the evaluated JSON files. They look like this:

```javascript
{
  "success": true,
  "totalHits": 92054,
  "Results": [
    {
      "subject": "OCTOBER 17 PRESS GUIDANCE FOR THE EAP REGION",
      "documentClass": "5-FY2014",
      "pdfLink": "DOCUMENTS/5-FY2014/F-2011-05467/DOC_0C05140032/C05140032.pdf",
      "originalLink": null,
      "docDate": "1995-10-17T04:00:00.000Z",
      "postedDate": "2014-05-13T04:00:00.000Z",
      "from": "STATE",
      "to": "ALEAP",
      "messageNumber": "1995STATE246360",
      "caseNumber": "F-2011-05467"
    },
    // ... 199 other results...
  ],
  "queryText": "*",
  "fieldMatch": "false",
  "response": "SUCCESS"
}
```

### Cleaning it up and downloading the documents

The Python scraper reads those page files in, and makes a `document.json` file for each result in the page, in its own predictably named directory. An individual `document.json` looks like this:

```json
{
  "caseNumber": null,
  "docDate": "1989-03-07T05:00:00.000Z",
  "documentClass": "StateChile3",
  "document_id": "DOCUMENTS\\StateChile3\\00008CE2",
  "file_type": "pdf",
  "filename": "00008CE2.pdf",
  "from": "SOFAER, ABRAHAM",
  "messageNumber": null,
  "originalLink": null,
  "pdfLink": "DOCUMENTS/StateChile3/00008CE2.pdf",
  "postedDate": "0001-01-01T05:00:00.000Z",
  "subject": "WITHDRAWN OF AGREEMENT AS PRESIDENT OF INTERNATIONAL COMMISSION",
  "to": "BASTID, SUZANNE",
  "url": "http://foia.state.gov/searchapp/DOCUMENTS/StateChile3/00008CE2.pdf"
}
```

The Python scraper, `data.py`, will then also download the document in the `url` field and save it to `document.pdf`. It will then extract text from that PDF and put it at `document.txt`.

By default, `data.py` will download PDFs and extract text, but this can be suppressed with `--dry_run`. It will not re-download PDFs that have already been downloaded -- to trigger a re-download, delete the directory containing the PDF. (It's trivial to restart the process using the cached `pages/` JSON anyway.)
