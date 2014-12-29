from unittest import TestCase
from unittest.mock import patch

import requests

import layer_with_reading_room as reading


class MockHistory():
    """ A mock 301 response. """

    def __init__(self):
        self.status_code = 301
        self.headers = {'Location': 'http://newurl.gov'}


class MockResponse():
    """ A mock requests response object that has a history, and so simulates a
    301 or 302 redirect """

    def __init__(self):
        f = MockHistory()
        self.history = [f]


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

        reading_room = 'http://foia.fcc.gov/'
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
            ['Reading Room', 'http://fbi.gov/reading-room-2000/'],
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
            'reading_rooms': [['reading', 'http://www.amtrak.com/foia/']]
        }
        new_links = [['reading', 'http://www.amtrak.com/foia/']]
        updated_agency = reading.update_links(agency_data, new_links)
        self.assertEqual([
            ['reading', 'http://www.amtrak.com/foia/']],
            updated_agency['reading_rooms'])

        new_links = [['FOIA library', 'http://www.amtrak.com/library/']]
        updated_agency = reading.update_links(agency_data, new_links)

        print(updated_agency)

        self.assertEqual([
            ['FOIA library', 'http://www.amtrak.com/library/'],
            ['reading', 'http://www.amtrak.com/foia/']],
            updated_agency['reading_rooms'])

        self.assertEqual([
            ['reading', 'http://www.amtrak.com/foia/']],
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
            [
                ['Reading Room', 'http://gsa.gov/foia/reading-room'],
                ['FOIA Library', 'http://gsa.gov/foia/library']],
            links)

    def test_remove_same_urls(self):
        links = [
            ['text one', 'http://testone.gov'],
            ['text two', 'http://testone.gov']]
        uniques = reading.uniquefy(links)
        self.assertEqual(len(uniques), 1)

        links = [
            ['text one', 'http://testone.gov/resources/foialibrary/'],
            ['text two', 'http://testone.gov/resources/foialibrary']]
        uniques = reading.uniquefy(links)
        self.assertEqual(len(uniques), 1)

    @patch('layer_with_reading_room.requests.get')
    def test_unique_links_redirect_exception_handling(self, req):
        req.side_effect = requests.exceptions.TooManyRedirects()

        links = [['text one', 'http://testone.gov/resources/foialibrary/']]
        uniques = reading.unique_links(links)
        self.assertEqual([], uniques)

    @patch('layer_with_reading_room.requests.get')
    def test_unique_links_connection_error(self, req):
        req.side_effect = requests.exceptions.ConnectionError
        links = [['text one', 'http://testone.gov/resources/foialibrary/']]
        uniques = reading.unique_links(links)
        self.assertEqual([], uniques)

    @patch('layer_with_reading_room.requests.get')
    def test_unique_links_redirect(self, req):
        req.return_value = MockResponse()
        links = [['text one', 'http://testone.gov/resources/foialibrary/']]
        uniques = reading.unique_links(links)
        self.assertEqual([['text one', 'http://newurl.gov']], uniques)

    @patch('layer_with_reading_room.requests.get')
    def test_unique_links_redirect_301(self, req):
        fake_response = MockResponse()
        fake_response.history[0].status_code = 302
        req.return_value = fake_response
        links = [['text one', 'http://testone.gov/resources/foialibrary/']]
        uniques = reading.unique_links(links)
        self.assertEqual([['text one', 'http://newurl.gov']], uniques)
