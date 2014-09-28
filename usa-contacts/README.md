# registry.usa.gov Agency Data

## Data directory

The files below are located in the data directory:

| File name      | Description   |
| -------------  |:-------------:|
| all_data.json      | Data pull from http://www.usa.gov/api/USAGovAPI/contacts.json/contacts |
| sample_data.json      | sample data from all_data.json |
| federal-offices.csv | data dump from SQL in https://github.com/GSA/project-open-data-dashboard#installation |


### Sample json from records

```
{'Alt_Language': [{'Id': '50101',
                   'Language': 'es',
                   'Name': 'Administración de Asuntos de Niños y Familias',
                   'URI': 'http://www.usa.gov/api/USAGovAPI/contacts.json/contact/50101'}],
 'Child': [{'Id': '49064',
            'Name': 'Administration for Native Americans',
            'URI': 'http://www.usa.gov/api/USAGovAPI/contacts.json/contact/49064'},
           {'Id': '49066',
            'Name': 'Administration on Developmental Disabilities',
            'URI': 'http://www.usa.gov/api/USAGovAPI/contacts.json/contact/49066'},
           {'Id': '49588',
            'Name': 'Office of Refugee Resettlement',
            'URI': 'http://www.usa.gov/api/USAGovAPI/contacts.json/contact/49588'}],
 'City': 'Washington',
 'Contact_Url': [{'Description': 'Contact the Administration for Children '
                                 'and Families (ACF)',
                  'Language': 'en',
                  'Url': 'http://www.acf.hhs.gov/about'},
                 {'Description': 'Child Support',
                  'Language': 'en',
                  'Url': 'http://www.acf.hhs.gov/programs/css/resource/state-and-tribal-child-support-agency-contacts'},
                 {'Description': 'Temporary Assistance for Needy Families '
                                 '(Welfare)',
                  'Language': 'en',
                  'Url': 'http://www.acf.hhs.gov/programs/ofa/help'},
                 {'Description': 'Report Child Abuse and Neglect',
                  'Language': 'en',
                  'Url': 'http://www.childwelfare.gov/pubs/reslist/rl_dsp.cfm?rs_id=5&rate_chno=11-11172'},
                 {'Description': 'Low Income Home Energy Assistance '
                                 'Program (LIHEAP)',
                  'Language': 'en',
                  'Url': 'http://1.usa.gov/n0kIxZ'}],
 'Description': 'The ACF funds state, territory, local, and tribal '
                'organizations to provide family assistance (welfare), child '
                'support, child care, Head Start, child welfare, and other '
                'programs relating to children and families.',
 'Id': '47994',
 'In_Person_Url': [{'Description': 'Head Start Program Locator',
                    'Language': 'en',
                    'Url': 'http://eclkc.ohs.acf.hhs.gov/hslc/HeadStartOffices'},
                   {'Description': 'Child Support Enforcement in Your State',
                    'Language': 'en',
                    'Url': 'http://www.acf.hhs.gov/programs/cse/extinf.html'},
                   {'Description': 'Contact Regional Offices',
                    'Language': 'en',
                    'Url': 'http://www.acf.hhs.gov/programs/oro'}],
 'Language': 'en',
 'Name': 'Administration for Children and Families (ACF)',
 'Parent': {'Id': '49021',
            'Name': 'U.S. Department of Health and Human Services (HHS)',
            'URI': 'http://www.usa.gov/api/USAGovAPI/contacts.json/contact/49021'},
 'Phone': ['(202) 401-9200'],
 'Source_Url': 'http://www.usa.gov/directory/federal/administration-for-children--families.shtml',
 'StateTer': 'DC',
 'Street1': "370 L'Enfant Promenade, SW",
 'Tollfree': ['(888) 289-8442 (Fraud Alert Hotline)'],
 'URI': 'http://www.usa.gov/api/USAGovAPI/contacts.json/contact/47994',
 'Web_Url': [{'Description': 'Administration for Children and Families '
                             '(ACF)',
              'Language': 'en',
              'Url': 'http://www.acf.hhs.gov/'}],
 'Zip': '20447'}
 ```
