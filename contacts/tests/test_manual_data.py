import os
from glob import glob
import yaml
from unittest import TestCase


def log_differences(manual_data, auto_data):
    return list(set(manual_data) - set(auto_data))


def log_duplicates(manual_data):
    seen = set()
    dups = list()
    for element in manual_data:
        if element not in seen:
            seen.add(element)
        else:
            dups.append(element)
    return dups


class ManualDataTests(TestCase):

    def test_for_inconsistencies(self):
        for filename in glob("manual_data" + os.sep + "*.yaml"):
            manual_dept_name, manual_office_names, dept_name, office_names = \
                None, None, None, None
            with open(filename) as f:
                yaml_data = yaml.load(f.read())
                if yaml_data.get('name'):
                    manual_dept_name = [yaml_data.get('name')]
            if yaml_data.get('departments'):
                manual_office_names = []
                for internal_data in yaml_data['departments']:
                    manual_office_names.append(internal_data['name'])
            with open(filename.replace('manual_data', 'data')) as f:
                yaml_data = yaml.load(f.read())
                dept_name = [yaml_data['name']]
            if yaml_data.get('departments'):
                office_names = []
                for internal_data in yaml_data['departments']:
                    office_names.append(internal_data['name'])

            if manual_office_names:
                differences = log_differences(
                    manual_data=manual_office_names,
                    auto_data=office_names)
                self.assertEqual(
                    differences, [],
                    msg="Invalid Office Name in %s" % filename)

                differences = log_duplicates(
                    manual_data=manual_office_names)

                self.assertEqual(
                    differences, [],
                    msg="Duplicated Office Name in %s" % filename)

            if manual_dept_name:
                differences = log_differences(
                    manual_data=manual_dept_name,
                    auto_data=dept_name)
                self.assertEqual(
                    differences, [],
                    msg="Invalid Top-level. Name in %s" % filename)
