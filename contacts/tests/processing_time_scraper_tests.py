import processing_time_scraper

from bs4 import BeautifulSoup
from unittest import TestCase

# HTTP requests are mocked out with vcrpy and requests
import vcr
import requests
my_vcr = vcr.VCR(cassette_library_dir='tests/fixtures/cassettes')


class ProcessingTimeScaperTests(TestCase):

    def test_parse_html(self):
        """ Parses data tables from foia.gov and return data """

        expected_data = {
            'federal retirement thrift investment board_frtib_2012': {
                'simple_median_days': '20',
                '': '',
                'simple_average_days': '27',
                'complex_lowest_days': '0',
                'expedited_processing_median_days': '0',
                'agency': 'FRTIB',
                'expedited_processing_average_days': '0',
                'complex_median_days': '0',
                'component': 'FRTIB',
                'year': '2012',
                'simple_lowest_days': '1',
                'simple_highest_days': '57',
                'complex_average_days': '0',
                'expedited_processing_highest_days': '0',
                'complex_highest_days': '0',
                'expedited_processing_lowest_days': '0'}}

        params = {"advanceSearch": "71001.gt.-999999"}
        params['requestYear'] = '2012'
        params['agencyName'] = 'FRTIB'

        with my_vcr.use_cassette('foia-gov-2012-FRTIB.yaml'):
            response = requests.get(
                processing_time_scraper.PROCESSING_TIMES_URL, params=params)
            html = response.text
            data = processing_time_scraper.parse_html(html, params, {})
            self.assertEqual(expected_data, data)

        # Won't break with empty tables
        params['requestYear'] = '2008'
        params['agencyName'] = 'RATB'

        with my_vcr.use_cassette('foia-gov-2008-RATB.yaml'):
            response = requests.get(
                processing_time_scraper.PROCESSING_TIMES_URL, params=params)
            html = response.text
            data = processing_time_scraper.parse_html(html, params, {})
            self.assertEqual({}, data)

    def test_get_key_values(self):
        """ Should convert a row in header into a unique key """

        test_row = BeautifulSoup('<span>1</span><span>Agency</span>', 'html.parser')
        test_row = test_row.findAll('span')
        key, value = processing_time_scraper.get_key_values(
            test_row, ['a', 'agency'], 'year', 'name')
        self.assertEqual(key, 'name_agency_year')

    def test_zip_and_clean(self):
        """ Returns a zipped dictionary with 0s coded as NAs """

        test_header = ['header 1', 'header 2', 'header 3']
        test_row = ['2.23', '0', 'NA']
        exp_data = {'header 1': '2.23', 'header 2': '0', 'header 3': 'NA'}
        result = processing_time_scraper.zip_and_clean(test_header, test_row)
        self.assertEqual(exp_data, result)

    def test_append_time_stats(self):
        """ Appends time stats data to dictionary"""

        test_yaml = {'name': "DOS", "other_data": "text blob"}
        test_data = {
            'DOSDOS_2013': {
                'simple_mean_days': '22', 'agency': 'DOS',
                'year': '2013', 'component': 'DOS', '': ''}}
        expected_data = {
            'name': "DOS", "other_data": "text blob",
            'request_time_stats': {
                '2013': {'simple_mean_days': '22'}}}
        result = processing_time_scraper.append_time_stats(
            test_yaml, test_data, "DOSDOS_2013", "_2013")
        self.assertEqual(expected_data, result)

    def test_get_years(self):
        """ Verify that the correct years are retrieved """

        with my_vcr.use_cassette("foia-gov-years.yaml"):
            response = requests.get(processing_time_scraper.YEARS_URL)
            html = response.text
            years = processing_time_scraper.get_years(html)
            years = sorted(years)
            self.assertEqual(['2008', '2009', '2010', '2011'], years[0:4])

    def test_clean_names(self):
        '''Should replace `-`, ` `, and `No. of` with underscores and
        make all elements of an array lower case'''

        test_array = [
            'Simple-Median No. of Days', 'Complex-Median No. of Days']
        expected_array = ['simple_median_days', 'complex_median_days']
        returned_array = processing_time_scraper.clean_names(test_array)
        self.assertEqual(returned_array, expected_array)

    def test_clean_html(self):
        """ Should replace `<1` with 1 """

        test_data = '<span><1</span>'
        returned_data = processing_time_scraper.clean_html(test_data)
        self.assertEqual(returned_data, '<span>less than 1</span>')

    def test_delete_empty_data(self):
        """ Should delete any items with a value of '' """

        test_data = {'A': '', 'B': 'value B'}
        returned_data = processing_time_scraper.delete_empty_data(test_data)
        self.assertEqual(returned_data, {'B': 'value B'})

    def test_clean_data(self):
        """
        Should deletes agency, year, and component attributes, which are not
        added to the yamls and also any attributes with empty values
        """
        test_data = {
            'simple_mean_days': '22', 'agency': 'DOS',
            'year': '2013',
            'component': 'DOS',
            '': ''}
        expected_data = {'simple_mean_days': '22'}
        returned_data = processing_time_scraper.clean_data(test_data)
        self.assertEqual(returned_data, expected_data)

    def test_load_mapping(self):
        """
        Test if mapping data is loaded properly
        """

        with my_vcr.use_cassette("foia-gov-years.yaml"):
            response = requests.get(processing_time_scraper.YEARS_URL)
            html = response.text
            years = processing_time_scraper.get_years(html)

        mapping = processing_time_scraper.load_mapping(years)

        # Check simple mapping (spelling error on foia.gov data)
        foia_data_key = 'bureau of alcohal, tobacco, ' + \
            'firearms and explosives_doj_2013'
        self.assertEqual(
            mapping[foia_data_key][0],
            'bureau of alcohol, tobacco, firearms, and explosives_doj_2013')

        # Check complex mapping instance (multiple names on foia.gov data)
        self.assertEqual(
            mapping['office of information and technology (005)_va_2013'],
            mapping['office of information and technology_va_2013'])

        # Check complex mapping instance (multiple names on foia_hub)
        yaml_key_1 = "surface transportation board_dot_2013"
        yaml_key_2 = "surface transportation board_stb_2013"
        foia_data_key = "surface transportation board_stb_2013"
        self.assertEqual(
            [yaml_key_1, yaml_key_2],
            sorted(mapping[foia_data_key]))

    def test_apply_mapping(self):
        """
        Verify that foia.gov/data keys are changed to keys compatiable with
        yaml keys
        """

        with my_vcr.use_cassette("foia-gov-years.yaml"):
            response = requests.get(processing_time_scraper.YEARS_URL)
            html = response.text
            years = processing_time_scraper.get_years(html)

        mapping = processing_time_scraper.load_mapping(years)

        # Check if items without mapping pass through without change
        foia_data_key = 'non_mapped_office_2013'
        test_data = {foia_data_key: {'simple_median_days': 3}}
        mapped_test_data = processing_time_scraper.apply_mapping(
            test_data, mapping)
        self.assertEqual(
            mapped_test_data[foia_data_key], test_data[foia_data_key])

        # Test simple transformations (spelling error on foia.gov data)
        foia_data_key = 'bureau of alcohal, tobacco, ' + \
            'firearms and explosives_doj_2013'
        yaml_key = 'bureau of alcohol, tobacco, firearms,' + \
            ' and explosives_doj_2013'
        test_data = {foia_data_key: {'simple_median_days': 3}}
        mapped_test_data = processing_time_scraper.apply_mapping(
            test_data, mapping)
        self.assertEqual(
            mapped_test_data[yaml_key], test_data[foia_data_key])

        # Test complex transformations (multiple names on foia.gov data)
        foia_data_key_1 = 'office of information and technology (005)_va_2013'
        foia_data_key_2 = 'office of information and technology_va_2008'
        yaml_key_1 = 'office of assistant secretary for ' + \
            'information and technology_va_2013'
        yaml_key_2 = 'office of assistant secretary for ' + \
            'information and technology_va_2008'
        test_data_1 = {foia_data_key_1: {'simple_median_days': 10}}
        test_data_2 = {foia_data_key_2: {'simple_median_days': 50}}
        mapped_test_data_1 = processing_time_scraper.apply_mapping(
            test_data_1, mapping)
        mapped_test_data_2 = processing_time_scraper.apply_mapping(
            test_data_2, mapping)

        self.assertEqual(
            mapped_test_data_1[yaml_key_1], test_data_1[foia_data_key_1])
        self.assertEqual(
            mapped_test_data_2[yaml_key_2], test_data_2[foia_data_key_2])

        # Test complex transformations (multiple names on foia.gov data)
        foia_data_key = 'surface transportation board_stb_2013'
        yaml_key_1 = 'surface transportation board_dot_2013'
        yaml_key_2 = 'surface transportation board_stb_2013'
        test_data = {foia_data_key: {'simple_median_days': 10}}
        mapped_test_data = processing_time_scraper.apply_mapping(
            test_data, mapping)

        self.assertEqual(
            mapped_test_data[yaml_key_1],
            mapped_test_data[yaml_key_2])
