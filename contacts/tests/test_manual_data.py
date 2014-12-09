import os
from glob import glob
import yaml
from unittest import TestCase


def log_differences(manual_data, auto_data, filename, level):
    return list(set(manual_data) - set(auto_data))


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
                    manual_office_names, office_names, filename, "office")
                self.assertEqual(differences, [])
            if manual_dept_name:
                differences = log_differences(
                    manual_dept_name, dept_name, filename, "department")
                self.assertEqual(differences, [])
