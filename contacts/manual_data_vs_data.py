import os
from glob import glob
import yaml
import logging


def log_differences(manual_data, auto_data, filename, level):
    differences = list(set(manual_data) - set(auto_data))
    if differences != []:
        logging.warning(
            "%s-level error in %s: %s",
            level, filename, ",".join(differences))


def search_for_inconsistencies():
    for filename in glob("manual_data" + os.sep + "*.yaml"):
        with open(filename) as f:
            yaml_data = yaml.load(f.read())
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

        log_differences(
            manual_office_names, office_names, filename, "office")
        if manual_dept_name[0]:
            log_differences(
                manual_dept_name, dept_name, filename, "department")

if __name__ == "__main__":
    """
    This script logs any instances where name from the manual yamls
    is not the data yamls.
    """
    logging.basicConfig(level=logging.INFO)
    search_for_inconsistencies()
