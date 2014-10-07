"""Collection of tweaks to fix FOIA data"""

# see http://foia.msfc.nasa.gov/reading.html
REPLACEMENTS = {
    "(256) 544-007 ": "(256) 544-0007 "
}


KEYWORDS = {
    'CIA': ['spies', 'espionage', 'counterintelligence'],
    'CFPB': ['HMDA', 'credit cards', 'mortgage'],
    'GSA': ['purchase cards', 'federal contracts', 'government forms'],
    'OSTP': ['white house', 'cto'],
}


#   Clearly not an elegant solution -- spell out all
#   departments/offices/components which should get the top_level flag
TOP_LEVEL = {
    'DHS': [
        'U.S. Citizenship & Immigration Services', 'U.S. Coast Guard',
        'U.S. Customs & Border Protection',
        'Federal Emergency Management Agency',
        'Federal Law Enforcement Training Center',
        'U.S. Immigration & Customs Enforcement',
        'United States Secret Service'],
    'DOC': [
        'Census Bureau', 'International Trade Administration',
        'Minority Business Development Agency',
        'National Institute of Standards and Technology',
        'National Technical Information Service',
        'National Oceanic and Atmospheric Administration',
        'U.S. Patent and Trademark Office'],
    'DoD': [
        'Office of the Secretary and Joint Staff',
        'Department of the Air Force', 'Department of the Army',
        'Department of the Navy', 'Marine Corps',
        'National Geographic Intelligence Agency', 'National Guard Bureau',
        'National Reconnaissance Office', 'National Security Agency'],
    'DOE': ['Office of Scientific and Technical Information'],
    'DOI': [
        'Bureau of Indian Affairs', 'Bureau of Land Management',
        'Bureau of Ocean Energy Management', 'Bureau of Reclamation',
        'Bureau of Safety and Environmental Enforcement',
        'U.S. Fish and Wildlife Service', 'National Park Service'],
    'DOJ': [
        'Office of the Attorney General',
        'Bureau of Alcohol, Tobacco, Firearms, and Explosives',
        'Drug Enforcement Administration', 'Federal Bureau of Investigation',
        'Federal Bureau of Prisons',
        'Office of Community Oriented Policing Services',
        'United States Marshals Service'],
    'DOT': [
        'Federal Aviation Administration',
        'National Highway Traffic Safety Administration'],
    'HHS': [
        'Administration for Community Living',
        'Agency for Healthcare Research and Quality',
        'Centers for Disease Control and Prevention',
        'Center for Medicare and Medicaid Services',
        'Food and Drug Administration',
        'Health Resources and Services Administration',
        'Indian Health Service', 'National Institutes of Health',
        'Substance Abuse and Mental Health Services Administration'],
    'NASA': ['Jet Propulsion Laboratory', 'NASA Shared Services Center'],
    'Treasury': [
        'Alcohol and Tobacco Tax and Trade Bureau',
        'Bureau of Engraving and Printing',
        'Comptroller of the Currency',
        'Financial Crimes Enforcement Network',
        'Internal Revenue Service',
        'United States Mint'],
    'U.S. DOL': [
        'Bureau of International Labor Affairs', 'Bureau of Labor Statistics',
        'Employee Benefits Security Administration',
        'Employment & Training Administration', 'Job Corps',
        'Mine Safety & Health Administration',
        'Occupational Safety & Health Administration'],
    'USPS': ['Postal Inspection Service'],
}
