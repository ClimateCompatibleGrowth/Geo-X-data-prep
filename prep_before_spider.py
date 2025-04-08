"""
@authors:
 - Alycia Leonard, University of Oxford, alycia.leonard@eng.ox.ac.uk
 - Samiyha Naqvi, University of Oxford, samiyha.naqvi@eng.ox.ac.uk
 - Lukas Schirren, Imperial College London, lukas.schirren@imperial.ac.uk

This script does three main preparation steps and one optional preparation 
step.

Optional step:
If hydropower is required, then this script will prepare data for hexagon 
preparation in SPIDER in the form of a GeoPackage file.
The outputs are saved to ccg-spider/prep/data/ and inputs_geox/final_data.

Main steps:
Firstly, it prepares data for land exclusion in GLAES, and hexagon preparation 
in SPIDER.
The raw inputs should be downloaded to data/ before execution.
The outputs are saved in glaes/data/ and ccg-spider/prep/data/ respectively.

Secondly, using GLAES, it implements land exclusions for the countries defined 
in the list 'country_names', and allocates PV and wind installations over the 
allowed area.
The outputs are saved as .shp files in input_glaes/processed/.

Lastly, this script makes SPIDER configs for each country in the 
'country_names' list.
It saves these files as "[CountryName]_config.yml" under ccg-spider/prep/.
"""
import argparse
import geopandas as gpd
import os
import pandas as pd
import pickle
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping
from unidecode import unidecode
import yaml

import glaes.glaes as gl
from utils import clean_country_name


def calculating_exclusions(glaes_data_path, country_name, EPSG, 
                           glaes_processed_path, turbine_radius):
    """
    Calculating exclusions using GLAES.

    ...
    Parameters
    ----------
    glaes_data_path : string
        Path to the folder where some files will be saved.
    country_name : string
        Name of country for file names.
    EPSG : integer
        Unique identifier representing coordinate systems and other geodetic 
        properties.
    glaes_processed_path : string
        Path to the folder where some files will be saved.
    turbine_radius : integer
        Turbine radius in meters used for spacing.
    """
    print(" - Initializing exclusion calculator...")
    ec = gl.ExclusionCalculator(os.path.join(glaes_data_path, f'{country_name}.geojson'), srs=EPSG, pixelSize=100)

    print(" - Applying exclusions - coast...")
    ec.excludeVectorType(os.path.join(glaes_data_path,  f'{country_name}_oceans.geojson'), buffer=250)

    print(" - Applying exclusions - herbaceous wetland...")
    ec.excludeRasterType(os.path.join(glaes_data_path, f'{country_name}_CLC.tif'), value=90, prewarp=True)

    print(" - Applying exclusions - built-up area...")
    ec.excludeRasterType(os.path.join(glaes_data_path, f'{country_name}_CLC.tif'), value=50, prewarp=True)
    print(" - Applying exclusions - permanent water bodies...")
    ec.excludeRasterType(os.path.join(glaes_data_path, f'{country_name}_CLC.tif'), value=80, prewarp=True)

    print(" - Saving excluded areas for wind as .tif file...")
    ec.save(os.path.join(glaes_processed_path,  f'{country_name}_wind_exclusions.tif'), overwrite=True)

    print(" - Distributing turbines and saving placements as .shp...")
    ec.distributeItems(separation=(turbine_radius * 10, turbine_radius * 5), axialDirection=45,
                    output=os.path.join(glaes_processed_path, f'{country_name}_turbine_placements.shp'))

    print(" - Applying exclusions - agriculture...")
    ec.excludeRasterType(os.path.join(glaes_data_path, f'{country_name}_CLC.tif'), value=40, prewarp=True)

    print(" - Saving excluded areas for PV as .tif file...")
    ec.save(os.path.join(glaes_processed_path, f'{country_name}_pv_exclusions.tif'), overwrite=True)

    print(" - Distributing pv plants and saving placements as .shp...")
    ec.distributeItems(separation=440, output=os.path.join(glaes_processed_path, f'{country_name}_pv_placements.shp'))

def replace_country(node, country_name):
    """
    Recursively replaces "Country" with the country name provided.

    ...
    Parameters
    ----------
    node : dictionary
        File contents that need to have "Country" replaced with the country
        name provided.
    country_name : string
        Name of country to be used as replacement.

    Returns
    -------
    node : dictionary
        File contents with the correct country name used.

    """
    if isinstance(node, dict):
        return {key: replace_country(value, country_name) for key, value in node.items()}
    elif isinstance(node, list):
        return [replace_country(item, country_name) for item in node]
    elif isinstance(node, str):
        return unidecode(node).replace("Country", country_name)
    else:
        return node
        

if __name__ == "__main__":
    # Parser set-up
    parser = argparse.ArgumentParser()
    parser.add_argument('countries', nargs='+', type=str,
                         help="<Required> Enter the country names you are preparing for.")
    parser.add_argument('--hydro', nargs='?', default=False, type=bool,
                        help="<Optional> Enter True if you need hydro to be prepared for. Default is False")
    args = parser.parse_args()

    # Define country name(s) to be used
    country_names = args.countries

    # Store paths to input files and folders
    dirname = os.path.dirname(__file__)
    data_path = os.path.join(dirname, 'data')
    regionPath = os.path.join(data_path, 'ne_50m_admin_0_countries', 'ne_50m_admin_0_countries.shp')
    clcRasterPath = os.path.join(data_path, "PROBAV_LC100_global_v3.0.1_2019-nrt_Discrete-Classification-map_EPSG-4326.tif")
    oceanPath = os.path.join(data_path, "GOaS_v1_20211214_gpkg", "goas_v01.gpkg")
    OSM_path = os.path.join(data_path, "OSM")
    config_name = "Country_config_hydro.yml" if args.hydro else "Country_config.yml"
    config_input_file_path = os.path.join(dirname, "inputs_spider", config_name)
    
    # Store paths to output folders
    glaes_data_path = os.path.join(dirname, 'glaes', 'glaes', 'data')
    spider_prep_data_path = os.path.join(dirname, 'ccg-spider', 'prep', 'data')
    glaes_processed_path = os.path.join(dirname, 'inputs_glaes', 'processed')
    spider_prep_path = os.path.join(dirname, "ccg-spider", "prep")
    geox_final_data_path = os.path.join(dirname, "inputs_geox/final_data")

    # Read shapefile of countries
    countries = gpd.read_file(regionPath).set_index('NAME')

    # Open and load the input config YAML file to be used to make the 
    # country-specific config YAML file
    with open(config_input_file_path, 'r') as file:
        config_data = yaml.load(file, Loader=yaml.FullLoader)
    
    # Define turbine radius in meters for spacing.
    # This is NREL_ReferenceTurbine_2020ATB_4MW - https://nrel.github.io/turbine-models/2020ATB_NREL_Reference_4MW_150.html
    # Other options:
    # Vestas_V80_2MW_gridstreamer - https://en.wind-turbine-models.com/turbines/19-vestas-v80-2.0, turbine_radius = 80
    # Enercon_E126_7500kW - https://www.thewindpower.net/turbine_en_225_enercon_e126-7500.php, turbine_radius = 127
    turbine_radius = 150

    # Loop through a list of country names
    for country_name in country_names:
        country_name_clean = clean_country_name(country_name)

        # Optional prep step - creating hydropower geopackage file
        if args.hydro:
            print(f"Creating Geopackage file for {country_name_clean}...")
            input_path = os.path.join(data_path, f"{country_name_clean}_hydropower_plants.csv") 
            output_path = os.path.join(spider_prep_data_path, f"{country_name_clean}_hydropower_dams.gpkg")
            final_data_output_path  = os.path.join(geox_final_data_path, f"{country_name_clean}_hydropower_dams.gpkg")

            # Read data from CSV
            data = pd.read_csv(input_path)

            # Select relevant columns
            data = data[['id', 'lat', 'lon', 'name', 'type', 
                        'capacity', 'avg_annual_generation_GWh', 
                        'head', 'country_code']]

            # Ensure numeric conversion for relevant columns
            data['lon'] = pd.to_numeric(data['lon'], errors='coerce')
            data['lat'] = pd.to_numeric(data['lat'], errors='coerce')
            data['capacity'] = pd.to_numeric(data['capacity'], errors='raise')

            # Drop rows with missing coordinates
            data = data.dropna(subset=['lon', 'lat'])

            ######## Data Preparation ########
            # Filter for existing plants
            data_existing = data.dropna(subset=['head'])
            print(f"Number of missing 'head' values: {data_existing['head'].isna().sum()}")

            ######## Export GeoPackage ########
            gdf = gpd.GeoDataFrame(
                data_existing,
                geometry=gpd.points_from_xy(data_existing.lon, data_existing.lat)
            )

            gdf.set_crs(epsg=4326, inplace=True)
            gdf.to_file(output_path, layer='dams', driver="GPKG")
            gdf.to_file(final_data_output_path, layer='dams', driver="GPKG")

            print(f"GeoPackage file successfully created for {country_name_clean}\n")


        # Step 1 - preparing files for glaes and spider
        print(f"Preparing spider and glaes data files for {country_name_clean}...")

        # Grab country boundaries
        country = countries.loc[[f'{country_name_clean}'], :]

        # Caculating glaes data files
        # Calculate UTM zone based on representative point of country
        representative_point = country.representative_point().iloc[0]
        latitude, longitude = representative_point.y, representative_point.x
        EPSG = int(32700 - round((45 + latitude) / 90, 0) * 100 + round((183 + longitude) / 6, 0))
        with open(os.path.join(glaes_data_path, f'{country_name_clean}_EPSG.pkl'), 'wb') as file:
            pickle.dump(EPSG, file)

        # Reproject country to UTM zone
        country.to_crs(epsg=EPSG, inplace=True)
        country.to_file(os.path.join(glaes_data_path, f'{country_name_clean}.geojson'), driver='GeoJSON', encoding='utf-8')

        # Buffer the "country" polygon by 1000 meters to create a buffer zone
        country_buffer = country['geometry'].buffer(10000)
        country_buffer.make_valid()
        country_buffer.to_file(os.path.join(glaes_data_path, f'{country_name_clean}_buff.geojson'), driver='GeoJSON', encoding='utf-8')

        # Reproject GOAS to UTM zone of country
        GOAS = gpd.read_file(oceanPath)
        country_buffer = country_buffer.to_crs(epsg=4326)
        GOAS.to_crs(epsg=4326, inplace=True)
        GOAS_country = gpd.clip(GOAS, country_buffer)
        GOAS_country['geometry'].make_valid()
        # Reconvert to country CRS? Check it makes no difference in distance outputs. GLAES seems happy with 4326.
        GOAS_country.to_file(os.path.join(glaes_data_path, f'{country_name_clean}_oceans.geojson'), driver='GeoJSON', encoding='utf-8')

        # Calculating spider data files
        # Save oceans to gpkg for spider
        GOAS_country.to_file(os.path.join(spider_prep_data_path, f'{country_name_clean}_oceans.gpkg'), driver='GPKG', encoding='utf-8')

        # Save OSM layers in 4236 gpkgs for spider
        OSM_country_path = os.path.join(OSM_path, f"{country_name_clean}")

        OSM_waterbodies = gpd.read_file(os.path.join(OSM_country_path, 'gis_osm_water_a_free_1.shp'))
        OSM_waterbodies.to_file(os.path.join(spider_prep_data_path, f'{country_name_clean}_waterbodies.gpkg'), driver='GPKG', encoding='utf-8')
        OSM_roads = gpd.read_file(os.path.join(OSM_country_path, f'gis_osm_roads_free_1.shp'))
        OSM_roads.to_file(os.path.join(spider_prep_data_path, f'{country_name_clean}_roads.gpkg'), driver='GPKG', encoding='utf-8')
        OSM_waterways = gpd.read_file(os.path.join(OSM_country_path, 'gis_osm_waterways_free_1.shp'))
        OSM_waterways.to_file(os.path.join(spider_prep_data_path, f'{country_name_clean}_waterways.gpkg'), driver='GPKG', encoding='utf-8')

        # Convert country back to EPSG 4326 to trim CLC and save this version for SPIDER as well
        country.to_crs(epsg=4326, inplace=True)
        country.to_file(os.path.join(spider_prep_data_path, f'{country_name_clean}.gpkg'), driver='GPKG', encoding='utf-8')

        # Open the CLC GeoTIFF file for reading
        with rasterio.open(clcRasterPath) as src:
            # Mask the raster using the vector file's geometry
            out_image, out_transform = mask(src, country.geometry.apply(mapping), crop=True)
            # Copy the metadata from the source raster
            out_meta = src.meta.copy()
            # Update the metadata for the clipped raster
            out_meta.update({
                'height': out_image.shape[1],
                'width': out_image.shape[2],
                'transform': out_transform
            })

            # Save the clipped raster as a new GeoTIFF file
            with rasterio.open(os.path.join(glaes_data_path, f'{country_name_clean}_CLC.tif'), 'w', **out_meta) as dest:
                dest.write(out_image)

        print(f"Finished preparing glaes and spider data files for {country_name_clean}\n")


        # Step 2 - running glaes
        print(f"Calculating land exclusions for {country_name_clean}...")

        # Load the pickled EPSG code for the country
        with open(os.path.join(glaes_data_path, f'{country_name_clean}_EPSG.pkl'), 'rb') as file:
            EPSG = pickle.load(file)

        calculating_exclusions(glaes_data_path, country_name_clean, EPSG, glaes_processed_path, turbine_radius)
        print("Finished calulcating land exclusions\n")
     

        # Step 3 - creating spider config files
        print(f'Preparing config file for {country_name_clean}...')

        current_data = replace_country(config_data, country_name_clean)

        output_file = f"{country_name_clean}_config.yml"
        with open(os.path.join(spider_prep_path, output_file), 'w', encoding='utf-8') as file:
            yaml.dump(current_data, file, default_flow_style=False, allow_unicode=True)

        print(f'Config file is created and saved as "{output_file}"')



