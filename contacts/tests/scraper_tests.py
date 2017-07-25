from bs4 import BeautifulSoup
from mock import patch
from unittest import TestCase

import os
import scraper
import yaml

# HTTP requests are mocked out with vcrpy and requests
import vcr
my_vcr = vcr.VCR(cassette_library_dir='tests/fixtures/cassettes')


class ScraperTests(TestCase):

    def test_populate_parent(self):
        agency_data = {
            'name': 'Best agency',
            'description': "The most important agency.",
            'departments': [
                {
                    'name': 'department one',
                    'emails': ['department.one@agency.gov'],
                    'keywords': ['department one things'],
                },
                {
                    'name': "I don't know which office",
                    'emails': ['hq@agency.gov'],
                    'phone': '202-555-5555',
                    'office_url': 'http://office.url',
                    'person_name': 'Joe Bureaucrat'
                }
            ]
        }
        populated = scraper.populate_parent(agency_data)
        self.assertEqual(len(populated['departments']), 1)
        self.assertEqual(populated['name'], 'Best agency')
        self.assertEqual(populated['phone'], '202-555-5555')
        self.assertEqual(populated['person_name'], 'Joe Bureaucrat')
        self.assertEqual(populated['emails'], ['hq@agency.gov'])
        self.assertEqual(populated['office_url'], 'http://office.url')

    def test_all_but_unknown(self):
        agency_data = {
            'departments': [
                {
                    'name': 'department one',
                    'emails': ['department.one@agency.gov'],
                    'keywords': ['department one things'],
                },
                {
                    'name': "I don't know which office",
                    'emails': ['hq@agency.gov']
                }
            ]
        }
        departments = scraper.all_but_unknown(agency_data)
        self.assertEqual(len(departments), 1)
        self.assertEqual(departments[0]['name'], 'department one')

    def test_get_unknown_office_details(self):
        agency_data = {
            'emails': ['foia@agency.gov'],
            'common_requests': ['spaceship plans'],
            'keywords': ['purchase card use', 'government forms'],
            'name': 'Best agency',
            'description': "The most important agency.",
            'departments': [
                {
                    'name': 'department one',
                    'emails': ['department.one@agency.gov'],
                    'keywords': ['department one things'],
                },
                {
                    'name': "I don't know which office",
                    'emails': ['hq@agency.gov']
                }
            ]
        }
        unknown = scraper.get_unknown_office_details(agency_data)
        self.assertEqual(
            unknown,
            {
                'name': "I don't know which office",
                'emails': ['hq@agency.gov']})

    def test_update_list_in_dict(self):
        original = {'keywords': ['accounting', 'estates']}
        scraper.update_list_in_dict(
            original, 'keywords', ['accounting', 'employment', 'courts'])

        self.assertEqual(
            original['keywords'],
            ['accounting', 'courts', 'employment', 'estates'])

        original = {}
        scraper.update_list_in_dict(original, 'emails', ['email@agency.gov'])
        self.assertEqual(original['emails'], ['email@agency.gov'])

    def test_actual_apply(self):
        agency_data = {
            'emails': ['foia@agency.gov'],
            'common_requests': ['spaceship plans'],
            'keywords': ['purchase card use', 'government forms'],
            'name': 'Best agency',
            'description': "The most important agency.",
            'departments': [
                {
                    'name': 'department one',
                    'emails': ['department.one@agency.gov'],
                    'keywords': ['department one things'],
                },
                {
                    'name': 'department two',
                    'emails': ['department.two@agency.gov']
                }
            ]
        }

        manual_data = {
            'no_records_about': ['aliens'],
            'emails': ['public.liaison@agency.gov'],
            'description': 'One of the most important agencies',
            'common_requests': ['travel data'],
            'keywords': ['election data', 'courts'],
            'departments': [
                {
                    'name': 'department one',
                    'top_level': True,
                    'emails': ['onefoia@agency.gov'],
                    'keywords': ['first things']}
            ]
        }

        applied = scraper.actual_apply(agency_data, manual_data)

        # New keywords added, but emails overwritten.
        self.assertEqual(
            applied['emails'],
            ['public.liaison@agency.gov'])
        self.assertEqual(
            applied['keywords'],
            [
                'courts', 'election data',
                'government forms', 'purchase card use'])
        self.assertEqual(
            applied['common_requests'],
            ['spaceship plans', 'travel data'])

        self.assertEqual(applied['no_records_about'], ['aliens'])
        self.assertEqual(
            applied['description'],
            'One of the most important agencies')

        department_names = [d['name'] for d in applied['departments']]
        self.assertEqual(
            department_names, ['department one', 'department two'])

        for d in applied['departments']:
            if d['name'] == 'department one':
                self.assertEqual(
                    d['emails'],
                    ['onefoia@agency.gov'])

                self.assertEqual(
                    d['keywords'],
                    ['department one things', 'first things'])

                self.assertTrue(d['top_level'])

            if d['name'] == 'department two':
                self.assertEqual({
                    'name': 'department two',
                    'emails': ['department.two@agency.gov']}, d)

    def test_read_manual_data(self):
        scraper.save_agency_data(
            'TEST', {'name': 'Test Agency'}, data_directory='/tmp/test/')
        data = scraper.read_manual_data('TEST', manual_data_dir='/tmp/test')
        self.assertEqual({'name': 'Test Agency'}, data)

    def test_agency_yaml_filename(self):
        filename = scraper.agency_yaml_filename('/tmp', 'TEST')
        self.assertEqual('/tmp/TEST.yaml', filename)

    def test_save_agency_data(self):
        scraper.save_agency_data(
            'TEST', {'name': 'Test Agency'}, data_directory='/tmp/test/')
        self.assertTrue(os.path.isfile('/tmp/test/TEST.yaml'))
        f = open('/tmp/test/TEST.yaml', 'r')
        test_data = yaml.load(f)
        f.close()
        self.assertEqual({'name': 'Test Agency'}, test_data)

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
        doc = BeautifulSoup(html, 'html.parser')
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
            </div>""", 'html.parser')
        lines, ps = scraper.clean_paragraphs(doc)
        self.assertEqual(lines, ['Content 1', 'Content 2', 'Content 3'])

    def test_clean_phone_number(self):
        """Test various phone formats and make sure bad formats produce
        errors"""
        for line in ("+4 123-456-7890", "4-(123) 456 7890", "41234567890"):
            self.assertEqual(
                "+4 123-456-7890", scraper.clean_phone_number(line))
        for line in ("  123-456-7890", "(123) 456 7890", "1234567890"):
            self.assertEqual("123-456-7890", scraper.clean_phone_number(line))
        for line in ("Other", "123-4567", "1234-5679-0"):
            self.assertRaises(Exception, scraper.clean_phone_number, line)
        # Test for extensions
        test_lines = (
            "(928) 779-2727, ext. 145",
            "(928) 779-2727, (ext. 145)",
            "(928) 779-2727 ext. 145")
        for line in test_lines:
            self.assertEqual(
                "928-779-2727 x145", scraper.clean_phone_number(line))

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
        ps = [BeautifulSoup(p, 'html.parser') for p in ps]
        emails = scraper.find_emails(lines, ps)
        self.assertEqual(["a@b.com", "c@d.com", "e@f.info", "g@h.io"],
                         emails)

        emails = scraper.find_emails(lines[:1], ps[:1])
        self.assertEqual([], emails)

        lines = ["Off hand reference to email"]
        ps = [BeautifulSoup("<p>Off hand reference to email</p>", 'html.parser')]
        self.assertRaises(Exception, scraper.find_emails, lines, ps)

    def test_extract_numbers(self):
        """ Verify that phone numbers are extracted and added to list"""

        phone_str = "(928) 779-2727, ext. 145"
        expected_output = ['928-779-2727 x145']
        self.assertEqual(expected_output,
                         scraper.extract_numbers(phone_str))

        # Still extracts 2 numbers even if their formatting is ugly
        phone_str += ", (928) 779-1111,, (ext. 145)"
        expected_output.append('928-779-1111 x145')
        self.assertEqual(expected_output,
                         scraper.extract_numbers(phone_str))

        # Won't extract incorrect phone numbers
        phone_str += ", (928) 779-111"
        self.assertEqual(expected_output,
                         scraper.extract_numbers(phone_str))

        phone_str = " (202) 663-4634, (202) 663-7026 (TTY)'"
        expected_output = ['202-663-4634', '202-663-7026 (TTY)']
        self.assertEqual(expected_output,
                         scraper.extract_numbers(phone_str))

    def test_organize_contact(self):
        """ Test if contacts are extracted an organized correctly """

        # Regular contact
        contact_str = "Denise Garrett, Phone: (202) 707-6800"
        self.assertEqual(
            {'name': 'Denise Garrett', 'phone': ['202-707-6800']},
            scraper.organize_contact(contact_str))

        # Contact with multiple numbers
        contact_str = "Denise Garrett, Phone: (202) 707-6800, (202) 700-6811"
        self.assertEqual(
            {
                'name': 'Denise Garrett',
                'phone': ['202-707-6800', '202-700-6811']
            },
            scraper.organize_contact(contact_str))

        # Contact with no name e.i. service centers
        contact_str = "Phone: (202) 707-6800"
        self.assertEqual(
            {'phone': ['202-707-6800']},
            scraper.organize_contact(contact_str))

        # Contact with no phone number
        contact_str = "Denise Garrett, Phone: "
        self.assertEqual(
            {'name': 'Denise Garrett'},
            scraper.organize_contact(contact_str))

        # Contact with no `,` number
        contact_str = "Denise Garrett, Phone: (202) 707-6800"
        self.assertEqual(
            {'name': 'Denise Garrett', 'phone': ['202-707-6800']},
            scraper.organize_contact(contact_str))

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
        ps = [BeautifulSoup(p, 'html.parser') for p in ps]
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
            <p>1 congress street</p>
            <p>Washington, DC 20505</p>
            <p>(555) 111-2222 (Telephone)</p>
            <p>(555) 222-3333 (Fax)</p>
            <p><a href="mailto:foia@example.gov;other@example.com">
                foia@example.gov</a> (Request via Email)</p>
            <hr />
            <p><strong>FOIA Requester Service Center:</strong>
                Phone: (555) 333-4444
            <p><strong>FOIA Public Liaison:</strong>
                Mark Someone, Phone: (555) 444-5555
            <p><strong>Program Manager:</strong>
                Someone Else, Phone: (555) 555-6666
            <p><strong>Website: </strong>
                <a href="http://www.foia.example.gov/">
                    http://www.foia.example.gov/</a>
            </p></blockquote></div>""", 'html.parser')
        result = scraper.parse_department(html, "Agency X")
        self.assertEqual(result['name'], "Agency X")
        self.assertEqual(
            result['address'],
            {
                'address_lines': ['Jane Smith', 'Awesome Person'],
                'zip': '20505',
                'street': '1 congress street',
                'city': 'Washington',
                'state': 'DC'
            })
        self.assertEqual(result['phone'], "555-111-2222")
        self.assertEqual(result['fax'], "555-222-3333")
        self.assertEqual(result['emails'],
                         ["foia@example.gov", "other@example.com"])
        self.assertEqual(result['service_center'], {'phone': ['555-333-4444']})
        self.assertEqual(
            result['public_liaison'],
            {'name': 'Mark Someone', 'phone': ['555-444-5555']})
        self.assertEqual(
            result['misc']['Program Manager'],
            {'phone': ['555-555-6666'], 'name': 'Someone Else'})
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
        result = scraper.parse_agency("AAA", BeautifulSoup(html, 'html.parser'))
        self.assertEqual(result['abbreviation'], "AAA")
        self.assertEqual(result['name'], "An Agency")
        self.assertEqual(result['description'], 'Some Description')
        self.assertEqual(2, len(result['departments']))
        hq_call, chicago_call = parse_department.call_args_list
        self.assertEqual(hq_call[0][0]['id'], "1")
        self.assertEqual(hq_call[0][1], "Headquarters")
        self.assertEqual(chicago_call[0][0]['id'], "2")
        self.assertEqual(chicago_call[0][1], "Chicago Branch")

    def test_agency_url(self):
        """Verify that agency abbreviations are getting converted into a URL"""
        self.assertTrue("agency=ABCDEF" in scraper.agency_url("ABCDEF"))
        self.assertTrue("agency=A+B+C+D" in scraper.agency_url("A B C D"))

    def test_address_list_to_dict(self):
        """ Verify that addresses are organized correctly """
        # Test simple address
        address_list = [
            "Martha R. Sell", "FOIA Assistant", "Suite 500",
            "2300 Clarendon Boulevard", "Arlington, VA 22201"]
        address_dict = {
            'state': 'VA',
            'address_lines': ['Martha R. Sell', 'FOIA Assistant', 'Suite 500'],
            'city': 'Arlington',
            'street': '2300 Clarendon Boulevard',
            'zip': '22201'}
        self.assertEqual(
            scraper.address_list_to_dict(address_list), address_dict)

        address_list.remove("Suite 500")
        address_dict['address_lines'].remove("Suite 500")
        self.assertEqual(
            scraper.address_list_to_dict(address_list), address_dict)

        # Test more complex addresses
        address_list = [
            "FOIA Contact", "1400 K Street, NW", "Washington , DC 20424"]
        address_dict = {
            'state': 'DC',
            'address_lines': ['FOIA Contact'],
            'city': 'Washington',
            'street': '1400 K Street, NW',
            'zip': '20424'}
        self.assertEqual(
            scraper.address_list_to_dict(address_list), address_dict)

        address_list.pop()
        address_list.append("Washington , DC 20424")
        self.assertEqual(
            scraper.address_list_to_dict(address_list), address_dict)

        address_list.pop()
        address_list.append("Washington , DC  20424")
        self.assertEqual(
            scraper.address_list_to_dict(address_list), address_dict)
