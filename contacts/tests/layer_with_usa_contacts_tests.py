import layer_with_usa_contacts as usa_layer
import os

from unittest import TestCase


class USALayerTests(TestCase):

    def test_clean_name(self):
        """
        Ensure that name cleaner removes extraneous elements in
        order to allow agency/office names to match
        """

        # Testing name with extraneous elements
        name_1 = 'U.S. Agency & Office - Headquarters'
        name_2 = 'Department of Agency and Office'
        self.assertEqual(
            usa_layer.clean_name(name_1), usa_layer.clean_name(name_2))

        # Testing replacements
        name_1 = 'AMTRAK'
        name_2 = 'National Railroad Passenger Corporation'
        self.assertEqual(
            usa_layer.clean_name(name_1), usa_layer.clean_name(name_2))

        # Testing two names with multiple extraneous elements
        name_1 = 'Department of the Air Force - Headquarters/ICIO (FOIA)'
        name_2 = 'U.S. Air Force'
        self.assertEqual(
            usa_layer.clean_name(name_1), usa_layer.clean_name(name_2))

        # Testing two names with multiple extraneous elements
        name_1 = 'U.S. Navy'
        name_2 = 'Department of the Navy - Main Office'
        self.assertEqual(
            usa_layer.clean_name(name_1), usa_layer.clean_name(name_2))

        # Testing two names with multiple extraneous elements
        name_1 = 'American Battle Monuments Commission'
        name_2 = 'American Battle Monuments Commission'
        self.assertEqual(
            usa_layer.clean_name(name_1), usa_layer.clean_name(name_2))

    def test_extract_abbreviation(self):
        """ Test if abbrivations are extracted properly from name """

        # No abbreviation
        name = "Test Agency"
        exp_abb = usa_layer.extract_abbreviation(name)
        self.assertEqual(exp_abb, None)

        # With abbreviation
        name = "Test Agency (TA)"
        exp_abb = usa_layer.extract_abbreviation(name)
        self.assertEqual(exp_abb, "TA")

    def test_create_contact_dict(self):
        """ Checks to make sure contact dict created properly """
        data = {
            'Name': 'Test Agency',
            'Description': 'Des',
            'Id': 1,
            'Language': 'en',
        }
        expected_dict = {'description': 'Des', 'usa_id': 1}
        self.assertEqual(usa_layer.create_contact_dict(data), expected_dict)

    def test_transform_json_data(self):
        """ Checks that json data is transformed correctly """

        data = [
            {
                'Name': 'Test Agency',
                'Description': 'Des',
                'Id': 1,
                'Language': 'en',
            }
        ]
        expected_output = {
            'Test Agency': {'description': 'Des', 'usa_id': 1},
        }
        self.assertEqual(usa_layer.transform_json_data(data), expected_output)

        # Testing Non-english records
        data = [
            {
                'Name': 'Test Agency',
                'Description': 'Des',
                'Id': 1,
                'Language': 'sp',
            }
        ]
        expected_output = {}
        self.assertEqual(usa_layer.transform_json_data(data), expected_output)

        # Testing agency with abbreviation
        data = [
            {
                'Name': 'Test Agency (TA)',
                'Description': 'Des',
                'Id': 1,
                'Language': 'en',
            }
        ]
        expected_output = {
            'Test Agency': {
                'abbreviation': 'TA', 'description': 'Des', 'usa_id': 1},
        }
        self.assertEqual(usa_layer.transform_json_data(data), expected_output)

        # Testing agencies with synonym
        data[0].update({'Synonym': ['Agency Test']})
        expected_output = {
            'Test Agency': {
                'abbreviation': 'TA', 'description': 'Des', 'usa_id': 1},
            'Agency Test': {
                'abbreviation': 'TA', 'description': 'Des', 'usa_id': 1},
        }
        self.assertEqual(usa_layer.transform_json_data(data), expected_output)

    def test_update_dict(self):

        new_data = {'usa_id': '1'}
        old_data = {}
        expected_data = {'usa_id': '1'}

        self.assertEqual(
            usa_layer.update_dict(old_data=old_data, new_data=new_data),
            expected_data
        )

        new_data.update({'description': 'des'})
        expected_data.update({'description': 'des'})
        self.assertEqual(
            usa_layer.update_dict(old_data=old_data, new_data=new_data),
            expected_data
        )

        new_data.update({'abbreviation': 'A'})
        expected_data.update({'abbreviation': 'A'})
        self.assertEqual(
            usa_layer.update_dict(old_data=old_data, new_data=new_data),
            expected_data
        )

    def test_write_yaml(self):
        """ Test if yaml file is written """

        usa_layer.write_yaml('test_yaml.yaml', {'test_key': 'test_value'})
        self.assertTrue(os.path.isfile('test_yaml.yaml'))
        os.remove('test_yaml.yaml')

    def test_get_api_data(self):
        """Test if data is retrived correctly"""

        test_site = "http://www.usa.gov/api/USAGovAPI/contacts.json"
        test_site += "/contact/48005"
        test_cache = "tests/fixtures/cassettes/test_cache"
        data = usa_layer.get_api_data(url=test_site, cache=test_cache)
        self.assertTrue("Census" in data.keys())

    def test_patch_yamls(self):
        """ Test if yaml files are correctly updated """

        test_site = "http://www.usa.gov/api/USAGovAPI/contacts.json"
        test_site += "/contact/48005"
        test_cache = "tests/fixtures/cassettes/test_cache"
        data = usa_layer.get_api_data(url=test_site, cache=test_cache)
        data.update({'Commerce': {'usa_id': '1111'}})

        patcher = usa_layer.patch_yamls(
            data=data, directory="tests/fixtures/cassettes/test_yaml.yaml")
        for patched_yaml in patcher:
            self.assertTrue(
                'usa_id' in patched_yaml[0])
            self.assertTrue(
                'usa_id' in patched_yaml[0].get('departments')[0])
            self.assertTrue(
                'description' in patched_yaml[0].get('departments')[0])
