# -*- coding: utf-8 -*-
"""
Created on Wed Oct 19 11:21:15 2023

@author: Alycia Leonard, University of Oxford

prep_after_spider.py

This script does three main prep steps.

Firstly, it joins the outputs from GLAES to the hexagons produced by SPIDER for input to GEOH2.
The inputs are the SPIDER hex.geojson file and the GLAES pv_placements.shp and turbine_placements.shp files
The output is a hexagon file where a count of turbine and pv installations is attached to the hexagons saved in Data.

Secondly, it assigns interest rate to different hexagons for different technology categories
based on their country.

Lastly, this script removes the duplicated hexagons that belong to country/countries
which are not the desired country.

"""

import argparse
import geopandas as gpd
import json
import os

from utils import clean_country_name

def combine_glaes_spider(hex, wind_points, pv_points):
    """
    Combining the glaes and spider file into one hexagon file.
    """
    print(" - Joining turbine locations...")
    # Spatial join the wind points to the polygons
    spatial_join = gpd.sjoin(wind_points, hex, how='left', predicate='within')

    # Group by polygon and count the points within each polygon
    wind_point_counts = spatial_join.groupby('index').size()

    # Merge the point counts with the 'hex' GeoDataFrame based on the index
    hex['theo_turbines'] = wind_point_counts

    # If some polygons have no points, fill their 'point_count' with 0
    hex['theo_turbines'] = hex['theo_turbines'].fillna(0)

    print(" - Joining pv locations...")
    # Spatial join the pv points to the polygons
    spatial_join = gpd.sjoin(pv_points, hex, how='left', predicate='within')

    # Group by polygon and count the points within each polygon
    pv_point_counts = spatial_join.groupby('index').size()

    # Merge the point counts with the 'hex' GeoDataFrame based on the index
    hex['theo_pv'] = pv_point_counts

    # If some polygons have no points, fill their 'point_count' with 0
    hex['theo_pv'] = hex['theo_pv'].fillna(0)

def assign_country(hexagons, world):
    """
    Assigns interest rate to different hexagons for different 
    technology categories based on their country.

    ...
    Parameters
    ----------
    hexagons : geodataframe
        Hexagon file from data folder
    world : geodataframe
        World dataset

    Returns
    -------
    hexagons_with_country : geodataframe
        Modified hexagons
    """
    hexagons.to_crs(world.crs, inplace=True)
    countries = world.drop(columns=[
                                    'pop_est', 
                                    'continent', 
                                    'iso_a3', 
                                    'gdp_md_est',
                                    ]
                            )
    countries = countries.rename(columns={'name':'country'})
    hexagons_with_country = gpd.sjoin(hexagons, countries, op='intersects') # changed from "within"
    
    # Clean up slightly by removing index_right
    hexagons_with_country = hexagons_with_country.drop('index_right', axis=1)

    return hexagons_with_country

def remove_extra_hexagons(output_hexagon_path, country_name_clean):
    """
    Removes duplicated hexagons.

    ...
    Parameters
    ----------
    output_hexagon_path : string
        File path to output hexagon file
    country_parameters : dataframe
        Country file from parameters

    Returns
    -------
    hexagons : geodataframe
        Modified hexagons
    """
    with open(output_hexagon_path, 'r') as file:
        hexagons = json.load(file)

    copied_list = hexagons["features"].copy()

    for feature in copied_list:
        if feature['properties']['country'] != country_name_clean:
            hexagons['features'].remove(feature)

    return hexagons

def update_hexagons(hexagons, output_hexagon_path):
    """
    Updates hexagon file with the new information
    """
    if isinstance(hexagons, dict):
            with open(output_hexagon_path, 'w') as file:
                json.dump(hexagons, file)
    elif not hexagons.empty:
        hexagons.to_file(f"{output_hexagon_path}", driver="GeoJSON")
    else:
        print(" ! Hex GeoDataFrame is empty. This can happen when your country \
              is much smaller than the hexagon size you have used in Spider. \
              Please use smaller hexagons in Spider and retry. Not saving to \
              GeoJSON.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('countries', nargs='+', type=str,
                         help="<Required> Enter the country names you are prepping")
    parser.add_argument('-ic', '--isocodes', nargs='+', type=str,
                        help="<Required> Enter the ISO codes for the country names you are prepping, respectively.")
    args = parser.parse_args()

    if not args.isocodes:
        parser.error('Please enter the ISO codes. This will be used in naming the final file.')

    # Define country name (used for output filenames)
    country_names = args.countries

    # Get path to this file
    dirname = os.path.dirname(__file__)

    # Counter to iterate through ISO codes
    iso_count=0

    # create a for loop that can loop through a list of country names
    for country_name in country_names:
        # Get country names without accents, spaces, apostrophes, or periods for loading files
        country_name_clean = clean_country_name(country_name)

        print(f"Combining GLAES and SPIDER data for {country_name_clean}!")

        # Get paths
        hex_path = os.path.join(dirname, "ccg-spider", "prep", f"{country_name_clean}_hex.geojson")
        wind_path = os.path.join(dirname, "inputs_glaes", "processed", f"{country_name_clean}_turbine_placements.shp")
        pv_path = os.path.join(dirname, "inputs_glaes", "processed", f"{country_name_clean}_pv_placements.shp")
        save_path = os.path.join(dirname, "inputs_geox", "data", f"{country_name_clean}_hex_final.geojson")

        # Load all files and convert all to the country's CRS
        print(" - Loading files...")
        hex = gpd.read_file(hex_path)
        wind_points = gpd.read_file(wind_path)
        pv_points = gpd.read_file(pv_path)
        hex.to_crs(pv_points.crs, inplace=True)

        combine_glaes_spider(hex, wind_points, pv_points)

        print(" - Done! Saving to GeoJSON...")

        update_hexagons(hex, save_path)
        
        # From the main prep file from the main geoh2 repo
        print("Prepping file...")
        hexagons = gpd.read_file(f"inputs_geox/data/{country_name_clean}_hex_final.geojson")
        world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres')) # may need to switch to higher res
        
        output_hexagon_path = f"inputs_geox/data/hex_final_{args.isocodes[iso_count]}.geojson"
        iso_count+=1

        hexagons_with_country = assign_country(hexagons, world)
        update_hexagons(hexagons_with_country, output_hexagon_path)

        # Finish off with the removing extra hexagons.
        final_hexagons = remove_extra_hexagons(output_hexagon_path, country_name_clean)
        update_hexagons(final_hexagons, output_hexagon_path)
        print("File prepped.")
