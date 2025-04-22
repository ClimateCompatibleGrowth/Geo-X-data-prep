# Geo-X-data-prep
Spatial data preparation tools for [Geo-X](https://github.com/ClimateCompatibleGrowth/Geo-X) users. 
The Geo-X library requires spatial hexagon files for the area of interest with several spatial parameters attached as an input. 
These scripts are designed to assist in creating these input data. They allow users to move from raw data inputs to a Geo-X-ready hexagon input by interfacing with the Global Land Availability of Energy Systems ([GLAES](https://github.com/FZJ-IEK3-VSA/glaes/tree/master/)) and Spatially Integrated Development of Energy and Resources ([SPIDER](https://github.com/carderne/ccg-spider/tree/main)).
___
## 1 Installation instructions

### 1.1 Clone the repository and submodules
First, clone the repository and initialise the submodules in one step:
```
/your/path % git clone --recurse-submodules https://github.com/ClimateCompatibleGrowth/Geo-X-data-prep.git
```
After cloning, navigate to the top-level folder of the repository.

### 1.2 Install Python dependencies
The Python package requirements to use these tools are in the `environment.yaml` file. 
You can install these requirements in a new environment using `mamba` package and environment manager (installation instructions [here](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html)): 
```
.../Geo-X-data-prep % mamba env create -f environment.yaml
```
This new environment can be activated using:
```
.../Geo-X-data-prep % mamba activate prep
```
Make sure to deactivate the environment before proceeding to the next step.

### 1.3 Install SPIDER environment
You will need to create a separate environment for the SPIDER submodule to work.

Firstly, navigate to the `ccg-spider/prep` folder:
```
.../Geo-X-data-prep % cd ccg-spider/prep
```
Next, create a new environment using your package and environment manager. Below shows how to, using `mamba`:
```
.../prep % mamba create -n spider
```
Next, activate the environment using:
```
.../prep % mamba activate spider
```
Next, install some necessary packages:
```
.../prep % mamba install pip gdal
```
Next, install the SPIDER requirements:
```
.../prep % pip install -e .
```
You should now have a fully functioning environment named `spider`. You can deactivate this for now and return to the top-level of the repository.
___
## 2 Preparing input data
> [!NOTE]
> Where `COUNTRY NAME` is used, make sure to replace it with the country name spelling that matches those used in the Natural Earth country boundaries shapefile (downloaded in step 2.1).

### 2.1 Input data
Before running the preparation scripts, some data must be downloaded and placed in the `data` folder. 

- The Global Oceans and Seas GeoPackage file can be downloaded from: https://www.marineregions.org/downloads.php
- The country boundaries shapefile can be downloaded from: https://www.naturalearthdata.com/downloads/50m-cultural-vectors/50m-admin-0-countries-2/
- OpenStreetMap Shapefile layers can be downloaded from (.shp.zip): https://download.geofabrik.de/
- The Corine Land Cover dataset (PROBAV_LC100_global_v3.0.1_2019-nrt_Discrete-Classification-map_EPSG-4326.tif) can be downloaded from: https://zenodo.org/records/3939050

Extra information:
- For the Global Oceans and Seas GeoPackage file, place the downloaded `GOaS_v1_20211214_gpkg` folder into the `data` folder.
- For the OpenStreetMap files, extract the contents from the downloaded folder into a subfolder as follows `data/OSM/[COUNTRY NAME]` for each country.
- For the files from Natural Earth Data, place the downloaded `ne_50m_admin_0_countries` folder into the `data` folder.

>[!IMPORTANT]
>Ensure that the config file you are using, either `Country_config.yml` or `Country_config_hydro.yml`, located in the `inputs_spider` folder, contains all the details you want SPIDER to use. Any removal or addition of features will require modification of the Geo-X codebase.

### 2.2 Optional input data
#### 2.2.1 Hydropower input data
If you want hydropower to be used as a generator, you will need another input file. In the `data` folder, there is a template that can be filled in and name updated. It should be named `[COUNTRY NAME]_hydropower_plants.csv` and kept in the `data` folder.

You can also use files from open-source datasets like the [Hydropower Database](https://github.com/energy-modelling-toolkit/hydro-power-database). You must rename the file to `[COUNTRY NAME]_hydropower_plants.csv` and ensure that the column titles match those in the template file. Extra columns do not need to be deleted, but they will not be taken into consideration when creating the GeoPackage file.

Input Data Requirements:
- The script is designed for datasets containing:
  - Latitude & Longitude (plant location)
  - Installed capacity (MW)
  - Annual generation (GWh)
  - Plant type (e.g., HDAM, HPHS,...)
  - Hydraulic head (m)

#### 2.2.2 Slope-exclusion input data
Slope-exclusion requires two input data files that must be downloaded and renamed:
- The country boundary GeoJSON file for each country can be downloaded from: [opendatasoft](https://public.opendatasoft.com/explore/dataset/world-administrative-boundaries/export/). Place each GeoJSON file into the `Slope-Exclusion/data` folder and rename to `[COUNTRY NAME]_boundary.geojson`.
- A 3-arc-second resolution conditioned Digital Elevation Model (DEM) file can be downloaded from: [HydroSHEDS](https://www.hydrosheds.org/hydrosheds-core-downloads). Place the downloaded conditioned DEM file, for each continent you require, in the `Slope-Exclusion/data` folder and rename to `[CONTINENT NAME]_full_dem.tif`, where `CONTINENT NAME` is the name of the continent that the TIF file contains.

>[!NOTE]
>The above naming conventions will allow you to place several files to run for several countries. At this point, each country will have to be run separately for some steps, this is expanded on in step 3.

## 3 Running data prep
There are two main scripts that are used, as well as the SPIDER submodule. As an optional step, the Slope-Exclusion submodule can be used before running any of the main steps to gather some input data for GLAES, which is part of the first main script.

>[!IMPORTANT]
>The size of the country can affect the runs as follows:
> - The two main scripts may take more than 10 minutes to complete.
> - SPIDER may crash. This is due to insufficient or failing computer memory (RAM) and can be solved by increasing your RAM or running on another computer with sufficient RAM.

### Optional step - Slope-Exclusion
>[!NOTE]
>This step must be repeated fully for each country that you wish to have slope exclusion files for.

Move to the `Slope-Exclusion` directory and activate the `prep` environment.

Take the following command, replace `[COUNTRY NAME]` and `[CONTINENT]` as necessary, and paste it into your terminal:
```
.../Slope-Exclusion % python clip_raster_to_boundary.py --raster data/[CONTINENT]_full_dem.tif --boundary data/[COUNTRY NAME]_boundary.geojson --output data/dem.tif
```

For the second and third command, there are some arguments that you need to pass via the terminal. They are:
- `--type`: (Only one required, `string` type) Should be either `solar`, `wind`, or `both`.
- `--solar-nea`: (Default is `6.28`, `float` type) The slope threshold for solar PV installations on north, east, and west-facing slopes.
- `--solar-s`: (Default is `33`, `float` type) The slope threshold for solar PV installations on south-facing slopes.
- `--wind-thresh`: (Default is `8.53`, `float` type) The slope threshold for wind turbine exclusion.
- `--sigma`: (Default is `1`, `float` type) The standard deviation of the Gaussian filter used to smooth the DEM.
- `--output`: (Default is `exclusion.tif`, `string` type) Name of output file.
Below are the recommended commands to get the files required for GLAES. You can change the float arguments to match the assumptions you wish to use.

Take the following command, replace `[COUNTRY NAME]` as necessary, and paste it into your terminal:
```
.../Slope-Exclusion % python exclude_slope.py --type solar --output [COUNTRY NAME]_slope_excluded_pv.tif
```

Take the following command, replace `[COUNTRY NAME]` as necessary, and paste it into your terminal:
```
.../Slope-Exclusion % python exclude_slope.py --type wind --output [COUNTRY NAME]_slope_excluded_wind.tif
```

The output files can be found in `Slope-Exclusion/output` and must be moved to `glaes/glaes/data`.

### 3.1 Run initial data prep before SPIDER
>[!NOTE]
>If you want to run multiple countries together, they must use the same config file. Otherwise, you can run each country separately, modifying the config file as necessary.

Activate the `prep` environment for this step, if not already activated from previous step.

There are some arguments that you need to pass via the terminal. They are:
- `countries`: (At least one required, `string` type) This should be the names of the countries you are preparing with a space between them. Make sure that the spellings used for country names match those used in the Natural Earth country boundaries shapefile.
- `--hydro`: (Default is `False`, `boolean` type) Only use this when you need to change to `True`.
- `-se`: (Default is `False`, `boolean` type) Only use this when you have used the Slope-Exclusion submodule and need to change to `True`.

Take the following command, replace `[COUNTRY NAME]` and keep/remove `--hydro` and `-se` as needed, and paste it into your terminal:
```
.../Geo-X-data-prep % python prep_before_spider.py [COUNTRY NAME] [COUNTRY NAME] --hydro True -se True
```
The above will first prepare a hydropower GeoPackage file, then pre-process the raw data, create a SPIDER config, and finally run GLAES. This will be done for each country provided.

### 3.2 Run SPIDER
>[!NOTE]
> Remember to deactivate the `prep` environment.

Now you will need to move to the `ccg-spider/prep` directory, activate the `spider` environment, and use the SPIDER CLI.

Take the following command, replace `[COUNTRY NAME]` with the name of the country you are studying without spaces or periods, and paste it into your terminal:
```
.../prep % gdal_rasterize data/[COUNTRY NAME].gpkg -burn 1 -tr 0.1 0.1 data/blank.tif && gdalwarp -t_srs EPSG:4088 data/blank.tif data/blank_proj.tif && spi --config=[COUNTRY NAME]_config.yml [COUNTRY NAME]_hex.geojson
```
This command must be run for **each** country.
This will produce a set of hexagon tiles for each country using the parameters in the `Country_config.yml` file.

>[!IMPORTANT]
> Do not use multiple `&&` symbols to run more than one country at once. Only one set of `blank.tif` and `blank_proj.tif` files will be generated based on the first country, which will lead to inaccurate hexagon files for subsequent countries.

### 3.3 Run data prep after SPIDER
>[!NOTE]
> Remember to move back to the top-level of the repository and deactivate the `spider` environment.

Activate the `prep` environment for this step.

There are some arguments that you need to pass via the terminal. They are:
- `countries`: (At least one required, `string` type) This should be the name of the countries you are preparing with a space between them. Make sure that the spellings used for country names match those used in the Natural Earth country boundaries shapefile.
- `-ic`: (At least one required, `string` type) This is the two-letter ISO code for your countries. They must be in the same order as your countries.

Take the following command, replace `[COUNTRY NAME]` and `[ISO CODE]` as necessary, and paste it into your terminal:
```
.../Geo-X-data-prep % python prep_after_spider.py [COUNTRY NAME] [COUNTRY NAME] -ic [ISO CODE] [ISO CODE]
```
The above will combine the SPIDER and GLAES files. It will then assign an interest rate to different hexagons for different technology categories based on their country. Lastly, this script removes the duplicated hexagons that belong to a country which are not the desired country. 

The final file will be saved as `hex_final_[COUNTRY ISO CODE].geojson` for each country in the `inputs_geox/final_data` folder. These `hex_final_[COUNTRY ISO CODE].geojson` files can be placed into a copy of the `Geo-X` repository in the `data` folder, as the baseline input data for modelling. 

If you set `hydro` to True, a `[COUNTRY NAME]_hydropower_dams.gpkg` file for each country will be generated into the `inputs_geox/final_data` folder. These files must be placed into the `data/hydro` folder of your `Geo-X` repository.

## Additional notes (Recommended to read at least once)
As the runs progress, you may not see all the files being generated, but rest assured they are there, taking up space. Once the runs have been completed, it's recommended to save the necessary files and review the listed folders below to delete any unnecessary files in order to free up space:
- `ccg-spider/prep`
- `ccg-spider/prep/data`
- `glaes/glaes/data`
- `inputs_geox/data`
- `inputs_geox/final_data`
- `inputs_glaes/processed`
- `Slope-Exclusion/data`
___

## Citation

If you decide to use this library and/or GeoH2, please kindly cite us using the following: 

*Halloran, C., Leonard, A., Salmon, N., Müller, L., & Hirmer, S. (2024). 
GeoH2 model: Geospatial cost optimization of green hydrogen production including storage and transportation. 
Pre-print submitted to MethodsX: https://doi.org/10.5281/zenodo.10568855. 
Model available on Github: https://github.com/ClimateCompatibleGrowth/GeoH2.*

```commandline
@techreport{halloran2024geoh2,
author  = {Halloran, C and Leonard, A and Salmon, N and Müller, L and Hirmer, S},
title   = {GeoH2 model: Geospatial cost optimization of green hydrogen production including storage and
transportation},
type = {Pre-print submitted to MethodsX},
year    = {2024},
doi = {10.5281/zenodo.10568855},
note = {Model available on Github at https://github.com/ClimateCompatibleGrowth/GeoH2.}
}
```
___

