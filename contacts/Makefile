all: contacts

contacts:
	python scraper.py
	python layer_with_csv.py
	# python layer_with_usa_contacts.py # USAGov contacts no longer supports this API
	python processing_time_scraper.py
	python keywords_from_fr.py
	python layer_with_reading_room.py

test:
	nosetests

setup:
	pip install -r requirements.txt

.PHONY: all contacts setup test
