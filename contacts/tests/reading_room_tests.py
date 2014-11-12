from unittest import TestCase
import get_reading_room as reading

class ReadingRoomTests(TestCase):

    def test_get_base_url(self):
        url = "http://example.gov/foia/reading/room/link"
        base = reading.get_base_url(url)
        self.assertEqual('http://example.gov/', base)

    def test_domains_match(self):
        website = 'http://www.fcc.gov/foia/'
        reading_room = 'http://www.cfpb.gov/foia/reading-room/'
        self.assertFalse(reading.domains_match(website, reading_room))

        reading_room = 'http://www.fcc.gov/oip/foia/reading-room'
        self.assertTrue(reading.domains_match(website, reading_room))

    def test_clean_link_text(self):
        link = """Here is a link to\n a reading room.   """
        
        self.assertEqual(
            'Here is a link to a reading room.',
            reading.clean_link_text(link))

    def test_get_absolute_url(self):
        class Link(object):
            def __init__(self):
                self.link = {}
            def get(self, name):
                return self.link[name]

        l = Link()
        l.link['href'] = "#tab-1"
        l.text = "FOIA Tab"
        self.assertEqual(
            None, reading.get_absolute_url(l, 'http://gsa.gov/foia/'))

        l = Link()
        l.link['href'] = '/reading-room-2000/'
        l.text = "Reading Room"
        self.assertEqual(
            ('Reading Room', 'http://fbi.gov/reading-room-2000/'), 
            reading.get_absolute_url(l, 'http://fbi.gov/foia/'))

        l = Link()
        l.link['href'] = '/'
        l.text = 'Main'
        self.assertEqual(
            None, reading.get_absolute_url(l, 'http://ssa.gov/foia'))

        l = Link()
        l.link['href'] = 'http://justice.gov/foia/'
        l.text = "FOIA"

        self.assertEqual(
            None, 
            reading.get_absolute_url(l, 'http://fbi.gov/rr'))

    def test_update_links(self):
        agency_data = {
            'reading_rooms': [('reading', 'http://www.amtrak.com/foia/')]
        }
        new_links = [('reading', 'http://www.amtrak.com/foia/')]
        updated_agency = reading.update_links(agency_data, new_links)
        self.assertEqual([
            ('reading', 'http://www.amtrak.com/foia/')],
            updated_agency['reading_rooms'])

        new_links = [('FOIA library', 'http://www.amtrak.com/library/')]
        updated_agency = reading.update_links(agency_data, new_links)

        self.assertEqual([
                ('FOIA library', 'http://www.amtrak.com/library/'),
                ('reading', 'http://www.amtrak.com/foia/')],
            updated_agency['reading_rooms'])

        self.assertEqual([
            ('reading', 'http://www.amtrak.com/foia/')],
            agency_data['reading_rooms'])

    def test_scrape_reading_room_links(self):
        html = """
            <p>
                <a href="http://gsa.gov/foia/reading-room">Reading Room</a>
            </p>
            <p> 
                <a href="http://gsa.gov/foia/library">FOIA Library</a>
            </p>
        """

        links = reading.scrape_reading_room_links(html, 'http://gsa.gov/foia')
        self.assertEqual(
            set([
                ('Reading Room', 'http://gsa.gov/foia/reading-room'),
                ('FOIA Library', 'http://gsa.gov/foia/library')]),
            links)
