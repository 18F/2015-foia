import requests
import yaml
from glob import glob
import os


def check_url(data, url_field):
    """ Actually check the URL and print out enough information to debug later.
    """
    try:
        r = requests.get(data[url_field], verify=False)
        if r.status_code != 200:
            print(r.status_code)
            print(data[url_field])
            print(data)
    except Exception as e:
        print(e)
        print(data[url_field])
        print(data)


def check_urls(data):
    """ Check the website and request form URLs."""
    if 'website' in data:
        check_url(data, 'website')
    if 'request_form' in data:
        check_url(data, 'request_form')


def check_all_urls(data):
    """ Check URLs for each agency, as well as those for each department. """
    check_urls(data)
    if 'departments' in data:
        for department in data['departments']:
            check_urls(department)


def check_all():
    for filename in glob('data' + os.sep + '*.yaml'):
        yaml_data = yaml.load(open(filename, 'r'))
        check_all_urls(yaml_data)


if __name__ == "__main__":
    check_all()
