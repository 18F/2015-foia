from copy import deepcopy
from unittest import TestCase

from bs4 import BeautifulSoup
from mock import patch

import layer_with_csv as layer
import scraper


class ScraperTests(TestCase):
    def test_agency_description(self):
        """Description should be pulled out and BRs should be converted"""
        html = """
            <h1>An Agency</h1>
            <h2>Blah blah</h2>
            <div id='0'>Default</div>
            <div id='1'>Description of office 1</div>
            <h2>About</h2>Line 1<br>Line 2<br><br>
            Line 3<br />
            Last Line
        """
        doc = BeautifulSoup(html)
        description = scraper.agency_description(doc)
        self.assertEqual(description, "Line 1\nLine 2\nLine 3\nLast Line")

    def test_clean_paragraphs(self):
        """Paragraphs should be pulled out and converted to text, disregarding
        empty/whitespace paragraphs"""
        doc = BeautifulSoup("""
            <div>
                <h1>Title</h1>
                <p>Content 1</p>
                <p />
                <p> &nbsp;</p>
                <p>\n\t</p>
                <p>Content 2
                <p><img />Content 3
            </div>""")
        lines, ps = scraper.clean_paragraphs(doc)
        self.assertEqual(lines, ['Content 1', 'Content 2', 'Content 3'])

    def test_phone(self):
        """Test various phone formats and make sure bad formats produce
        errors"""
        for line in ("+4 123-456-7890", "4-(123) 456 7890", "41234567890"):
            self.assertEqual("+4 123-456-7890", scraper.phone(line))
        for line in ("  123-456-7890", "(123) 456 7890", "1234567890"):
            self.assertEqual("123-456-7890", scraper.phone(line))
        for line in ("Other", "123-4567", "1234-5679-0"):
            self.assertRaises(Exception, scraper.phone, line)

    def test_split_address_from(self):
        """Address should be separated as soon as we encounter "service
        center", "fax", etc."""
        lines = ["Line 1", "Line 2", "1234567890 serVice CenTer", "Line 3"]
        addy, rest = scraper.split_address_from(lines)
        self.assertEqual(lines[:2], addy)
        self.assertEqual(lines[2:], rest)

        lines = ["Line 1\n\rLine 2\nfax", "fax 1234567890"]
        addy, rest = scraper.split_address_from(lines)
        self.assertEqual(["Line 1", "Line 2", "fax"], addy)
        self.assertEqual(lines[1:], rest)

    def test_find_emails(self):
        """Verify that email addresses can be pulled out (and split, if
        appropriate) from paragraphs"""
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
        """Three types of bold fields, simple key-value pairs (like 'notes'),
        url values (e.g. website, request form), and 'misc' -- everything
        else. Account for empty urls"""
        ps = [
            "<p>Intro <strong>Some Key:</strong> Some Value</p>",
            "<p><strong>Notes</strong> Some notes here</p>",
            "<p><strong>Website:</strong><a href='example.com'>here</a></p>",
            "<p><strong>Request Form: </strong><a href=''></a></p>",
            "<p><strong>FOIA Contact</strong> is John</p>"]
        ps = [BeautifulSoup(p) for p in ps]
        results = list(scraper.find_bold_fields(ps))
        self.assertEqual(results, [("misc", ("Some Key", "Some Value")),
                                   ("notes", "Some notes here"),
                                   ("website", "example.com"),
                                   ("request_form", "")])

    def test_parse_department_integration(self):
        """Integration test for the department div. Make sure that, given a
        blob of html, correct fields are pulled out. Use a mix of properly
        closed <p>s and not (this mixtures matches the live data)"""
        html = BeautifulSoup("""<div><blockquote>
            <p><strong>FOIA Contact:</strong> send to:</p>
            <p>Jane Smith</p>
            <p>Awesome Person</p>
            <p></p>
            <p>A Federal Agency</p>
            <p>Washington, DC 20505</p>
            <p>(555) 111-2222 (Telephone)</p>
            <p>(555) 222-3333 (Fax)</p>
            <p><a href="mailto:foia@example.gov;other@example.com">
                foia@example.gov</a> (Request via Email)</p>
            <hr />
            <p><strong>FOIA Requester Service Center:</strong>
                Phone: (555) 333-4444
            <p><strong>FOIA Public Liaison:</strong>
                Mark Someone, (555) 444-5555
            <p><strong>Program Manager:</strong>
                Someone Else, Phone: (555) 555-6666
            <p><strong>Website: </strong>
                <a href="http://www.foia.example.gov/">
                    http://www.foia.example.gov/</a>
            </p></blockquote></div>""")
        result = scraper.parse_department(html, "Agency X")
        self.assertEqual(result['name'], "Agency X")
        self.assertEqual(result['address'],
                         ["Jane Smith", "Awesome Person", "A Federal Agency",
                          "Washington, DC 20505"])
        self.assertEqual(result['phone'], "555-111-2222")
        self.assertEqual(result['fax'], "555-222-3333")
        self.assertEqual(result['emails'],
                         ["foia@example.gov", "other@example.com"])
        self.assertEqual(result['service_center'], "Phone: (555) 333-4444")
        self.assertEqual(result['public_liaison'],
                         "Mark Someone, (555) 444-5555")
        self.assertEqual(result['misc']['Program Manager'],
                         "Someone Else, Phone: (555) 555-6666")
        self.assertEqual(result['website'], "http://www.foia.example.gov/")

    @patch('scraper.parse_department')
    def test_parse_agency(self, parse_department):
        """Verify that the agency-specific fields (abbreviation, name,
        description) are pulled out, and that we are calling the
        parse_department function on the appropriate div. Include some messy
        HTML (e.g. empty link tag in the title, "Return to Top", etc. etc.)"""
        html = """<div><div><a><img />Print Selected Office</a></div></div>
                  <h1><a></a>An Agency</h1>
                  <div><img />
                    <p>Chief FOIA Officer: Some One, Officer</p>
                    <p><a><img />What do these FOIA terms mean?</a></p>
                  </div>
                  <h2><label for="ComponentsList">I want to:</label></h2>
                  <select id="ComponentsList">
                    <option value="0">Select an Office</option>
                    <option value="1">Headquarters</option>
                    <option value="2">Chicago Branch</option>
                  </select>
                  <div id="0">Div Zero</div>
                  <div id="1">Div One</div>
                  <div id="2">Div Two</div>
                  <p>&nbsp;</p>
                  <div class="lineshadow"></div>
                  <h2>About the this agency</h2>Some Description
                  <p align="right"><a href="#top">Return to Top</a></p>"""
        result = scraper.parse_agency("AAA", BeautifulSoup(html))
        self.assertEqual(result['abbreviation'], "AAA")
        self.assertEqual(result['name'], "An Agency")
        self.assertEqual(result['description'], 'Some Description')
        self.assertEqual(2, len(result['departments']))
        hq_call, chicago_call = parse_department.call_args_list
        self.assertEqual(hq_call[0][0]['id'], "1")
        self.assertEqual(hq_call[0][1], "Headquarters")
        self.assertEqual(chicago_call[0][0]['id'], "2")
        self.assertEqual(chicago_call[0][1], "Chicago Branch")

    @patch.dict('typos.KEYWORDS', {'AGENCY': ['keyword1', 'kw2']})
    def test_add_keywords(self):
        """This should only add keywords to the if the abbreviation is
        'AGENCY' and should not affect the dict otherwise."""
        result = scraper.add_keywords('NONAGENCY', {})
        self.assertEqual({}, result)
        result = scraper.add_keywords('AGENCY', {})
        self.assertEqual({'keywords': ['keyword1', 'kw2']}, result)

    @patch.dict('typos.TOP_LEVEL', {'AGENCY': ['HQ']})
    def test_add_top_level(self):
        """The 'top_level' flag should be set on configured departments"""
        agency = {'departments': [{'name': 'HQ'}, {'name': 'Other Q'}]}
        agency_orig = deepcopy(agency)
        result = scraper.add_top_level('NONAGENCY', agency)
        self.assertEqual(agency, agency_orig)   # Non-mutating
        depts = [d['top_level'] for d in result['departments']]
        self.assertEqual(depts, [False, False])

        result = scraper.add_top_level('AGENCY', agency)
        self.assertEqual(agency, agency_orig)   # Non-mutating
        depts = [d['top_level'] for d in result['departments']]
        self.assertEqual(depts, [True, False])

    def test_agency_url(self):
        """Verify that agency abbreviations are getting converted into a URL"""
        self.assertTrue("agency=ABCDEF" in scraper.agency_url("ABCDEF"))
        self.assertTrue("agency=A+B+C+D" in scraper.agency_url("A B C D"))


class LayerTests(TestCase):
    def test_address_lines(self):
        """Add lines for room number, street addy is present. Only add
        city/state/zip if all three are present."""
        row = {"Room Number": "", "Street Address": "", "City": "",
               "State": "", "Zip Code": ""}
        row["City"] = "Boston"
        self.assertEqual([], layer.address_lines(row))
        row["Zip Code"] = 90210
        self.assertEqual([], layer.address_lines(row))
        row["Street Address"] = "123 Maywood Dr"
        self.assertEqual(["123 Maywood Dr"], layer.address_lines(row))
        row["Room Number"] = "Apt B"
        self.assertEqual(["Apt B", "123 Maywood Dr"],
                         layer.address_lines(row))
        row["State"] = "XY"
        self.assertEqual(["Apt B", "123 Maywood Dr", "Boston, XY 90210"],
                         layer.address_lines(row))

    def test_contact_string(self):
        """Format name and phone information; check each combination"""
        row = {"Name": "", "Telephone": ""}
        self.assertEqual("", layer.contact_string(row))
        row["Name"] = "Bob Bobberson"
        self.assertEqual("Bob Bobberson", layer.contact_string(row))
        row["Telephone"] = "(111) 222-3333"
        self.assertEqual("Bob Bobberson, Phone: (111) 222-3333",
                         layer.contact_string(row))
        row["Name"] = ""
        self.assertEqual("Phone: (111) 222-3333", layer.contact_string(row))

    def test_patch_dict(self):
        """Verify fields are added, nothing gets overwritten, and misc fields
        are merged"""
        old_dict = {"a": 1, "b": 2, "misc": {"z": 100}}
        new_dict = {"b": 4, "c": 3, "misc": {"z": 999, "y": 99}}
        result = layer.patch_dict(old_dict, new_dict)
        self.assertEqual(result, {
            "a": 1, "b": 2, "c": 3, "misc": {"z": 100, "y": 99}})

    def test_patch_dict_noop(self):
        """If there are no new field, None is returned"""
        old_dict = {"a": 1, "b": 2}
        new_dict = {"b": 100}
        self.assertEqual(None, layer.patch_dict(old_dict, old_dict))
        self.assertEqual(None, layer.patch_dict(old_dict, new_dict))

    def empty_row(self):
        return {"Agency": "", "Department": "", "Name": "", "Title": "",
                "Room Number": "", "Street Address": "", "City": "",
                "State": "", "Zip Code": "", "Telephone": "", "Fax": "",
                "Email Address": "", "Website": "", "Online Request Form": "",
                "Notes": ""}

    def test_add_contact_info_agency(self):
        """Agency & Office should be added to `contact` dictionary if not
        present"""
        row = self.empty_row()
        row["Department"] = "ACRONYM"
        row["Agency"] = "Sewage Treatment"
        contact_dict = {}
        layer.add_contact_info(contact_dict, row)
        self.assertTrue("ACRONYM" in contact_dict)
        self.assertTrue("Sewage Treatment" in contact_dict["ACRONYM"])
        #   Adding again has no affect
        layer.add_contact_info(contact_dict, row)
        self.assertTrue("ACRONYM" in contact_dict)
        self.assertTrue("Sewage Treatment" in contact_dict["ACRONYM"])
        #   Adding another agency
        row["Agency"] = "Road Maintenance"
        layer.add_contact_info(contact_dict, row)
        self.assertTrue("ACRONYM" in contact_dict)
        self.assertTrue("Sewage Treatment" in contact_dict["ACRONYM"])
        self.assertTrue("Road Maintenance" in contact_dict["ACRONYM"])

    def test_add_contact_info_website(self):
        """Website field gets cleaned up -- verify it's not added unless it's
        in the right form"""
        row = self.empty_row()
        row["Department"] = "A"
        row["Agency"] = "B"
        contact_dict = {}
        layer.add_contact_info(contact_dict, row)
        self.assertFalse("website" in contact_dict["A"]["B"])

        row["Website"] = "http://"
        layer.add_contact_info(contact_dict, row)
        self.assertFalse("website" in contact_dict["A"]["B"])

        row["Website"] = "http://example.gov"
        layer.add_contact_info(contact_dict, row)
        self.assertEqual("http://example.gov",
                         contact_dict["A"]["B"]["website"])

    def test_add_contact_info_emails(self):
        """Each row that contains an email address should get added to the
        list"""
        row = self.empty_row()
        row["Department"] = "A"
        row["Agency"] = "B"
        contact_dict = {}
        layer.add_contact_info(contact_dict, row)
        self.assertEqual(contact_dict["A"]["B"]["emails"], [])

        row["Email Address"] = "a@b.com"
        layer.add_contact_info(contact_dict, row)
        self.assertEqual(contact_dict["A"]["B"]["emails"], ["a@b.com"])

        row["Email Address"] = "c@d.gov"
        layer.add_contact_info(contact_dict, row)
        self.assertEqual(contact_dict["A"]["B"]["emails"],
                         ["a@b.com", "c@d.gov"])

    def test_add_contact_info_people(self):
        """Verify that the title of a row indicates which field it should be
        placed in"""
        row = self.empty_row()
        row["Department"] = "A"
        row["Agency"] = "B"
        row["Name"] = "Ada"
        contact_dict = {}
        layer.add_contact_info(contact_dict, row)
        self.assertFalse("service_center" in contact_dict["A"]["B"])
        self.assertEqual(contact_dict["A"]["B"]["misc"], {})

        row["Title"] = "Awesome Person"
        layer.add_contact_info(contact_dict, row)
        self.assertFalse("service_center" in contact_dict["A"]["B"])
        self.assertEqual(contact_dict["A"]["B"]["misc"],
                         {"Awesome Person": "Ada"})

        row["Name"] = "Bob"
        row["Title"] = "FOIA Service Center Technician"
        layer.add_contact_info(contact_dict, row)
        self.assertEqual(contact_dict["A"]["B"]["service_center"], "Bob")
        self.assertEqual(contact_dict["A"]["B"]["misc"],
                         {"Awesome Person": "Ada"})