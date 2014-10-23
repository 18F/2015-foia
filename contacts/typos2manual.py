import scraper
import typos


if __name__ == "__main__":
    """ This one-time use script is designed to take everything in typos.py and
    create manual override YAML files for the agencies. """

    agencies = {}
        
    for agency in typos.KEYWORDS.keys():
        data = {}
        data = scraper.add_keywords(agency, data)
        agencies[agency] = data

    for agency in typos.TOP_LEVEL.keys():
        departments = []

        for department in typos.TOP_LEVEL[agency]:
            department = {'name': department, 'top_level':True}
            departments.append(department)

        data = agencies.get(agency, {})
        agencies[agency] = dict(data, departments=departments)

    for agency in agencies:
        scraper.save_agency_data(agency, agencies[agency], 'manual_data')
