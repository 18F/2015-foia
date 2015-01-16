from mock import Mock
from unittest import TestCase

import keywords_from_fr as fr


class FRTests(TestCase):
    """Tests keywords_from_fr"""
    def test_normalize_name(self):
        for old, new in (
            ('United States African Development Foundation',
                'AFRICAN DEVELOPMENT FOUNDATION'),
            ('Administration for Children and Families',
                'CHILDREN FAMILIES'),
            ('Export-Import Bank of the U.S.', 'EXPORTIMPORT BANK'),
            ('Department of the Army - Main Office', 'ARMY'),
            ('Centers for Disease Control', 'CENTER DISEASE CONTROL')
        ):
            self.assertEqual(fr.normalize_name(old), new)

    def test_fetch_page_dates(self):
        """Should compute the min and max day of each month"""
        client = Mock()
        fr.fetch_page(2003, 2, 1, client)
        self.assertTrue('2003-02-01' in str(client.get.call_args))
        self.assertTrue('2003-02-28' in str(client.get.call_args))
        self.assertFalse('2003-02-29' in str(client.get.call_args))
        fr.fetch_page(2004, 2, 1, client)
        self.assertTrue('2004-02-01' in str(client.get.call_args))
        self.assertFalse('2004-02-28' in str(client.get.call_args))
        self.assertTrue('2004-02-29' in str(client.get.call_args))

    def test_fetch_page_errors(self):
        """Should handle bad JSON and 500s"""
        client = Mock()
        response = Mock()
        client.get.return_value = response
        response.status_code = 500
        self.assertEqual({'results': []}, fr.fetch_page(2003, 2, 1, client))

        response.status_code = 200
        response.json.side_effect = ValueError
        self.assertEqual({'results': []}, fr.fetch_page(2003, 2, 1, client))

    def test_last_day_in_month(self):
        """Verify leap years, etc."""
        self.assertEqual(28, fr.last_day_in_month(2003, 2))
        self.assertEqual(29, fr.last_day_in_month(2004, 2))
        self.assertEqual(31, fr.last_day_in_month(2011, 1))

    def test_normalize_and_map(self):
        """should normalize keys w/ loosing data"""
        test_dict = {'A': {'datum1'}, 'B': {'datum2'}, 'a': {'datum3'}}
        expected_dict = {'A': {'datum1', 'datum3'}, 'B': {'datum2'}}
        self.assertEqual(expected_dict, fr.normalize_and_map(test_dict))
