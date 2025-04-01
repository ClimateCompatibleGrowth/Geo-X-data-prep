# -*- coding: utf-8 -*-
"""
Created on Mon Mar 10 2025

@author: Alycia Leonard, University of Oxford

prep_after_spider.py

This script does three main prep steps.

Firstly, it joins the outputs from GLAES to the hexagons produced by SPIDER for input to GEO-X.
The inputs are the SPIDER hex.geojson file and the GLAES pv_placements.shp and turbine_placements.shp files.
The output is a hexagon file where a count of turbine and pv installations is attached to the hexagons.

Secondly, it assigns interest rate to different hexagons for different technology categories
based on their country, saving the hexagons into a new file.

Lastly, this script removes the duplicated hexagons that belong to the country/countries
which are not the desired country and updates the file created in step two.

All files are saved to /inputs_geox/data.
"""

import argparse
import geopandas as gpd
import json
import os

from utils import clean_country_name

def combine_glaes_spider(hex, wind_points, pv_points):
    """
    Combining the glaes and spider files into one hexagon file.
    
    ...
    Parameters
    ----------
    hex : geodataframe
        Hexagon file from spider run.
    wind_points : geodataframe
        Wind placements file from glaes run.
    pv_points : geodataframe
        PV placements file from glaes run.

    Returns
    -------
    hex : geodataframe
        Combined hexagons.
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

    return hex

def assign_country(hexagons, world):
    """
    Assigns interest rate to different hexagons for different technology 
    categories based on their country.

    ...
    Parameters
    ----------
    hexagons : geodataframe
        Hexagon file from data folder.
    world : geodataframe
        World dataset.

    Returns
    -------
    hexagons_with_country : geodataframe
        Modified hexagons.
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
        File path to output hexagon file.
    country_name_clean : string
        Country name in a standardised format.

    Returns
    -------
    hexagons : geodataframe
        Modified hexagons.
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
    Updates hexagon file with the new information.

    ...
    Parameters
    ----------
    hexagons : geodataframe
        Hexagon file from data folder.
    output_hexagon_path : string
        File path to output hexagon file.
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
    # Parser set-up
    parser = argparse.ArgumentParser()
    parser.add_argument('countries', nargs='+', type=str,
                         help="<Required> Enter the country names you are preparing for.")
    parser.add_argument('-ic', '--isocodes', nargs='+', type=str,
                        help="<Required> Enter the ISO codes for the country names you are preparing for, respectively.")
    args = parser.parse_args()

    if not args.isocodes:
        parser.error('Please enter the ISO codes. This will be used in naming the final file.')

    # Define country name (used for naming files)
    country_names = args.countries

    # Get path to this file
    dirname = os.path.dirname(__file__)

    # Counter to iterate through ISO codes
    iso_count=0

    # Loop through a list of country names
    for country_name in country_names:
        # Get country names without accents, spaces, apostrophes, or periods for loading files
        country_name_clean = clean_country_name(country_name)

        print(f"Combining GLAES and SPIDER data for {country_name_clean}:")

        # Get paths
        hex_path = os.path.join(dirname, "ccg-spider", "prep", f"{country_name_clean}_hex.geojson")
        wind_path = os.path.join(dirname, "inputs_glaes", "processed", f"{country_name_clean}_turbine_placements.shp")
        pv_path = os.path.join(dirname, "inputs_glaes", "processed", f"{country_name_clean}_pv_placements.shp")
        save_path = os.path.join(dirname, "inputs_geox", "data", f"{country_name_clean}_hex_final.geojson")

        # Step 1 - combining glaes and spider files
        # Load all files and convert hex to the country's CRS
        print(" - Loading files...")
        hex = gpd.read_file(hex_path)
        wind_points = gpd.read_file(wind_path)
        pv_points = gpd.read_file(pv_path)
        hex.to_crs(pv_points.crs, inplace=True)

        hexagons = combine_glaes_spider(hex, wind_points, pv_points)

        update_hexagons(hexagons, save_path)
        print("Done! File saved \n")
                 
        # Step 2 - assigning interest rate to the hexagons
        print("Assigning interest rate to hexagons...")
        # May need to switch to higher res
        world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
        
        output_hexagon_path = f"inputs_geox/final_data/hex_final_{args.isocodes[iso_count]}.geojson"
        iso_count+=1

        hexagons_with_country = assign_country(hexagons, world)
        update_hexagons(hexagons_with_country, output_hexagon_path)
        print("Done! File saved \n")


        # Step 3 - finish off with removing duplicated hexagons
        print("Removing duplicated hexagons...")
        final_hexagons = remove_extra_hexagons(output_hexagon_path, country_name_clean)
        update_hexagons(final_hexagons, output_hexagon_path)
        print("Done! File saved")
