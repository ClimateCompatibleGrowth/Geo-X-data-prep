"""
@authors: 
 - Alycia Leonard, University of Oxford, alycia.leonard@eng.ox.ac.uk
 - Samiyha Naqvi, University of Oxford, samiyha.naqvi@eng.ox.ac.uk

A simple file used for shared functions.

Contains clean_country_name().
"""
from unidecode import unidecode

def clean_country_name(country_name):
    """
    Takes in a country name and standardises to a version without spaces, full-
    stops and apostrophes.

    ...
    Parameters
    ----------
    country_name : string
        Name of country to be standardised.
    """
    country_name_clean = unidecode(country_name)
    country_name_clean = country_name_clean.replace(" ", "")
    country_name_clean = country_name_clean.replace(".", "")
    country_name_clean = country_name_clean.replace("'", "")

    return country_name_clean