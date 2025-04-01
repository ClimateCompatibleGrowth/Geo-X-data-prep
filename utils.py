# -*- coding: utf-8 -*-
"""
Created on Wed Mar 19 2025

@authors: 
 - Alycia Leonard, University of Oxford
 - Samiyha Naqvi, University of Oxford

utils.py

A simple file used for shared functions.

Contains clean_country_name().
"""

from unidecode import unidecode

def clean_country_name(country_name):
    """
    Takes in country name and standardises to a "cleaner version"

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