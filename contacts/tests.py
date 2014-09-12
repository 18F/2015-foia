from unittest import TestCase

from bs4 import BeautifulSoup

import scraper


class ScraperTests(TestCase):
    def setUp(self):
        self.html = """
            <h1>An Agency</h1>
            <h2>I want to make a FOIA request to:
                <select>
                    <option value='0'>Select an Office</option>
                    <option value='1'>First Office</option>
                    <option value='2'>Second Office</option>
                </select>
            </h2>
            <div id='0'>Default</div>
            <div id='1'>Description of office 1</div>
            <div id='2'>Description of office 2</div>
            <h2>About</h2>Line 1<br>Line 2<br><br>Last Line
        """

    def test_agency_description(self):
        doc = BeautifulSoup(self.html)
        description = scraper.agency_description(doc)
        self.assertEqual(description, "Line 1\nLine 2\nLast Line")

    def test_clean_paragraphs(self):
        doc = BeautifulSoup("""
            <div>
                <h1>Title</h1>
                <p>Content 1</p>
                <p />
                <p> &nbsp;</p>
                <p>\n\t<p>
                <p>Content 2 </p>
            </div>""")
        lines, ps = scraper.clean_paragraphs(doc)
        self.assertEqual(lines, ['Content 1', 'Content 2'])

    def test_phone(self):
        for line in ("+4 123-456-7890", "4-(123) 456 7890", "41234567890"):
            self.assertEqual("+4 123-456-7890", scraper.phone(line))
        for line in ("  123-456-7890", "(123) 456 7890", "1234567890"):
            self.assertEqual("123-456-7890", scraper.phone(line))
        for line in ("Other", "123-4567", "1234-5679-0"):
            self.assertRaises(Exception, scraper.phone, line)

    def test_split_address_from(self):
        lines = ["Line 1", "Line 2", "1234567890 serVice CenTer", "Line 3"]
        addy, rest = scraper.split_address_from(lines)
        self.assertEqual(lines[:2], addy)
        self.assertEqual(lines[2:], rest)

        lines = ["Line 1\n\rLine 2\nfax", "fax 1234567890"]
        addy, rest = scraper.split_address_from(lines)
        self.assertEqual(["Line 1", "Line 2", "fax"], addy)
        self.assertEqual(lines[1:], rest)

    def test_find_emails(self):
        lines = ["Line 1", "Some email: ", "Then e-mails:", "Line 4"]
        ps = ["<p>Line 1</p>",
              "<p>Some email: <a href='mailto:a@b.com'>click</a></p>",
              "<p>Then e-mails:<a href='mailto:c@d.com;e@f.info;   g@h.io'>"
              + "email</a></p>",
              "<p>Line 4</p>"]
        ps = [BeautifulSoup(p) for p in ps]
        emails = scraper.find_emails(lines, ps)
        self.assertEqual(["a@b.com", "c@d.com", "e@f.info", "g@h.io"],
                         emails)

        emails = scraper.find_emails(lines[:1], ps[:1])
        self.assertEqual([], emails)

        lines = ["Off hand reference to email"]
        ps = [BeautifulSoup("<p>Off hand reference to email</p>")]
        self.assertRaises(Exception, scraper.find_emails, lines, ps)

    def test_find_bold_fields(self):
        ps = [
            "<p>Intro <strong>Some Key:</strong> Some Value</p>",
            "<p><strong>Notes</strong> Some notes here</p>",
            "<p><strong>Website:</strong> is <a href='example.com'>here</a>"
            + "</p>",
            "<p><strong>FOIA Contact</strong> is John</p>"]
        ps = [BeautifulSoup(p) for p in ps]
        results = list(scraper.find_bold_fields(ps))
        self.assertEqual(results, [("misc", ("Some Key", "Some Value")),
                                   ("notes", "Some notes here"),
                                   ("website", "example.com")])
