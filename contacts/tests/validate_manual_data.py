import os
from glob import glob
import yaml
import logging


def log_differences(manual_data, scraped_data):
    """
    Returns a list of differences between the manual and scraped data lists.
    """
    return list(set(manual_data) - set(scraped_data))


def log_duplicates(manual_data):
    """ Returns a list of duplicates """
    seen = set()
    dups = list()
    for element in manual_data:
        if element not in seen:
            seen.add(element)
        else:
            dups.append(element)
    return dups


def validate_manual_data():
    """
    Checks for duplicate and spelling inconsistencies departments in
    manual data
    """

    spelling_inconsistencies = 0
    duplicates = 0

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
            office_spelling_diffs = log_differences(
                manual_data=manual_office_names,
                scraped_data=office_names)
            if office_spelling_diffs:
                spelling_inconsistencies += 1
                logging.warning(
                    'Spelling Inconsistency in %s - %s',
                    filename, ", ".join(office_spelling_diffs))

            office_duplicates = log_duplicates(
                manual_data=manual_office_names)
            if office_duplicates:
                duplicates += 1
                logging.warning(
                    'Duplicates in %s - %s',
                    filename, ", ".join(office_duplicates))

        if manual_dept_name:
            dept_spelling_diffs = log_differences(
                manual_data=manual_dept_name,
                scraped_data=dept_name)
            if dept_spelling_diffs:
                spelling_inconsistencies += 1
                logging.warning(
                    'Spelling Inconsistency in %s - %s',
                    filename, ", ".join(dept_spelling_diffs))

    logging.info("Spelling Inconsistencies: %s", spelling_inconsistencies)
    logging.info("Duplicates: %s", duplicates)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    validate_manual_data()
