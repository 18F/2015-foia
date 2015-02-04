import layer_with_usa_contacts as usa_layer
import os

from unittest import TestCase


class USALayerTests(TestCase):

    def test_clean_name(self):
        name = 'U.S. Africa Command'
        exp_name = 'Africa Command'
        self.assertEqual(exp_name, usa_layer.clean_name(name))

    def test_extract_abbreviation(self):

        # No abbrivation
        name = "Test Agency"
        exp_name, exp_abb = usa_layer.extract_abbreviation(name)
        self.assertEqual(exp_name, name)
        self.assertEqual(exp_abb, None)

        # With abbrivation
        name = "Test Agency (TA)"
        exp_name, exp_abb = usa_layer.extract_abbreviation(name)
        self.assertEqual(exp_name, "Test Agency (TA)")
        self.assertEqual(exp_abb, "TA")

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

        # Testing Agency with Abbreviation
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

        usa_layer.write_yaml('test_yaml.yaml', {'test_key': 'test_value'})
        self.assertTrue(os.path.isfile('test_yaml.yaml'))
        os.remove('test_yaml.yaml')
