import os
from glob import glob
import yaml
import logging


def log_spelling_differences(manual_data, auto_data, error_msg):
    """ Warns users of spelling errors in manual data """
    spelling_error = list(set(manual_data) - set(auto_data))
    if spelling_error:
        logging.warning(error_msg + ": %s" % spelling_error)
        return 1
    else:
        return 0


def log_duplicates(manual_data, error_msg):
    """ Returns a list of duplicate values"""
    seen = set()
    dups = list()
    for element in manual_data:
        if element not in seen:
            seen.add(element)
        else:
            dups.append(element)
    if dups:
        logging.warning(error_msg + ": %s" % dups)
        return 1
    else:
        return 0


def validate_manual_data():
    """ Checks for duplicate and misspelled departments in manual data """

    office_spelling_errors = 0
    office_duplicate_errors = 0
    dept_spelling_errors = 0

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
            office_spelling_errors += log_spelling_differences(
                manual_data=manual_office_names,
                auto_data=office_names,
                error_msg="Invalid Office Name in %s" % filename)

            office_duplicate_errors += log_duplicates(
                manual_data=manual_office_names,
                error_msg="Duplicated Office Name in %s" % filename)

        if manual_dept_name:
            dept_spelling_errors += log_spelling_differences(
                manual_data=manual_dept_name,
                auto_data=dept_name,
                error_msg="Invalid Top-level. Name in %s" % filename)

    logging.info("%s spelling error(s) in yamls",
                 office_spelling_errors + dept_spelling_errors)

    logging.info("%s duplicate error(s) in yamls", office_duplicate_errors)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    validate_manual_data()
