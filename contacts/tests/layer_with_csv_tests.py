from unittest import TestCase

import layer_with_csv as layer


class LayerTests(TestCase):
    def test_organize_address(self):
        """Add lines for room number, street addy is present. Only add
        address if city/state/zip/street are present."""

        row = {"Room Number": "", "Street Address": "", "City": "",
               "State": "", "Zip Code": ""}
        row["City"] = "Boston"
        self.assertEqual(None, layer.organize_address(row))

        row['Zip Code'] = '90210'
        self.assertEqual(None, layer.organize_address(row))

        row['Street Address'] = '123 Maywood Dr'
        self.assertEqual(None,
                         layer.organize_address(row))

        row['Room Number'] = 'Apt B'
        self.assertEqual(None,
                         layer.organize_address(row))

        row['State'] = 'XY'
        expected_address_dict = {
            'address_lines': ['Apt B'], 'city': 'Boston', 'state': 'XY',
            'street': '123 Maywood Dr', 'zip': '90210'}
        self.assertEqual(expected_address_dict,
                         layer.organize_address(row))

        # In layer_with_csv street name is assumed correct
        row['Street Address'] = 'not a street'
        expected_address_dict['street'] = 'not a street'
        self.assertEqual(expected_address_dict,
                         layer.organize_address(row))

        # Zips are also cleaned up, but still assumed correct
        row['Zip Code'] = 20823.0
        expected_address_dict['zip'] = '20823'
        self.assertEqual(expected_address_dict,
                         layer.organize_address(row))

    def test_contact_string(self):
        """Format name and phone information; check each combination"""
        row = {"Name": "", "Telephone": ""}
        self.assertEqual({}, layer.contact_string(row))
        row["Name"] = "Bob Bobberson"
        self.assertEqual({'name': 'Bob Bobberson'}, layer.contact_string(row))
        row["Telephone"] = "(111) 222-3333"
        self.assertEqual({'name': 'Bob Bobberson', 'phone': ['111-222-3333']},
                         layer.contact_string(row))
        row["Name"] = ""
        self.assertEqual(
            {'phone': ['111-222-3333']}, layer.contact_string(row))
        row["Telephone"] = "(202) 218-7770 (ext. 7744), (202) 218-7970"
        row["Name"] = "Bob Bobberson"
        self.assertEqual(
            {
                'name': 'Bob Bobberson',
                'phone': ['202-218-7770 x7744', '202-218-7970']
            },
            layer.contact_string(row))

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
        #   Adding another agency with leading and trailing spaces
        row["Agency"] = "  Economic Development   "
        layer.add_contact_info(contact_dict, row)
        self.assertTrue("ACRONYM" in contact_dict)
        self.assertTrue("Sewage Treatment" in contact_dict["ACRONYM"])
        self.assertTrue("Road Maintenance" in contact_dict["ACRONYM"])
        self.assertTrue("Economic Development" in contact_dict["ACRONYM"])

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
                         {'Awesome Person': {'name': 'Ada'}})

        row["Name"] = "Bob"
        row["Title"] = "FOIA Service Center Technician"
        layer.add_contact_info(contact_dict, row)
        self.assertEqual(contact_dict["A"]["B"]["service_center"],
                         {'name': 'Bob'})
        self.assertEqual(contact_dict["A"]["B"]["misc"],
                         {'Awesome Person': {'name': 'Ada'}})
