import os
import sys
import yaml
from foia_hub.settings.default import BASE_DIR


DEFAULT_YAML_FOLDER = 'foia/contacts/data'


def _get_yaml_folder():
    return BASE_DIR.rstrip('/foia_hub').rstrip('foia-') + DEFAULT_YAML_FOLDER


def process_yaml_data(data_key):
    folder = _get_yaml_folder()

    count = 0
    for item in os.listdir(folder):
        data_file = os.path.join(folder, item)
        data = yaml.load(open(data_file))
        for rec in data['departments']:
            data_value = rec.get(data_key, None)

            if not data_value:
                # Count how many records are missing this value
                count += 1
            else:
                # Print out the values to the variance in the information.
                #print(data['name'])  # Get agency name
                print(data_value)

    print('------------------------------------------------------')
    print('Records without %s: %s' % (data_key, count))


if __name__ == "__main__":
    """
    This is a simple script to give some insight into the data in the yaml
    contacts folder. To run the script, pass the key at the dept level
    to return the values.

        python explorer.py request_form

    """
    data_key = sys.argv[1]
    process_yaml_data(data_key)
