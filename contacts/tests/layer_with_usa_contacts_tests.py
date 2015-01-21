from unittest import TestCase

import layer_with_usa_contacts as usa_layer


class USALayerTests(TestCase):
    def test_float_to_int_str(self):
        """should convert input to int (floor) then string when possible"""
        self.assertEqual('32', usa_layer.float_to_int_str(32.32))
        self.assertEqual('32', usa_layer.float_to_int_str(32.99))
        self.assertEqual(None, usa_layer.float_to_int_str(None))
        self.assertEqual('23', usa_layer.float_to_int_str("23.2"))
        self.assertEqual('23.2x', usa_layer.float_to_int_str("23.2x"))

    def test_extract_acronym(self):
        """extract one acroym, if it has two return 'massive error'"""

        self.assertEqual(
            "DOS", usa_layer.extract_acronym('Department of State (DOS)'))
        self.assertEqual(
            "", usa_layer.extract_acronym("Random Office"))
        self.assertEqual(
            "Massive Error",
            usa_layer.extract_acronym("Random Office (RO) (RO)"))

    def test_update_dict(self):
        """ Updates the new dictionary with ids, abbreviation, description
        and forms, but will not overwrite any descriptions """

        new_data = {
            'Deparment A': {'usa_id': '1', 'acronym': 'A'},
            'Deparment B': {
                'usa_id': '2', 'acronym': 'B',
                'description': 'next des.'}}

        old_data = {'name': 'Deparment A', 'description': "old desc."}
        old_data_expected = {
            'name': 'Deparment A', 'description': "old desc.",
            'usa_id': '1', 'abbreviation': 'A'}
        old_data, new_data = usa_layer.update_dict(old_data, new_data)
        self.assertEqual(old_data_expected, old_data)

        old_data = {'name': 'Deparment B'}
        old_data_expected = {
            'name': 'Deparment B', 'description': "next des.",
            'usa_id': '2', 'abbreviation': 'B'}
        old_data, new_data = usa_layer.update_dict(old_data, new_data)
        self.assertEqual(old_data_expected, old_data)
