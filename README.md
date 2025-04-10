# Geo-X-data-prep
Spatial data preparation tools for [Geo-X](https://github.com/ClimateCompatibleGrowth/Geo-X) users. 
The Geo-X library requires spatial hexagon files for the area of interest with several spatial parameters attached as an input. 
These scripts are designed to assist in creating these input data. They allow users to move from raw data inputs to a Geo-X-ready hexagon input by interfacing with the Global Land Availability of Energy Systems ([GLAES](https://github.com/FZJ-IEK3-VSA/glaes/tree/master/)) and Spatially Integrated Development of Energy and Resources ([SPIDER](https://github.com/carderne/ccg-spider/tree/main)).
___
## 1 Installation instructions

### 1.1 Clone the repository and submodules
First, clone the repository and initialise the submodules in one step:

`/your/path % git clone --recurse-submodules https://github.com/ClimateCompatibleGrowth/Geo-X-data-prep.git`

After cloning, navigate to the top-level folder of the repository.

### 1.2 Install Python dependencies
The Python package requirements to use these tools are in the `environment.yaml` file. 
You can install these requirements in a new environment using `mamba` package and environment manager (installation instructions [here](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html)): 

` .../Geo-X-data-prep % mamba env create -f environment.yaml`

This new environment can be activated using:

`.../Geo-X-data-prep % mamba activate prep`

Make sure to deactivate the environment before proceeding to the next step.

### 1.3 Install SPIDER environment
You will need to create a separate environment for the SPIDER submodule to work.

Firstly, navigate to the `ccg-spider/prep` folder:

`.../Geo-X-data-prep % cd ccg-spider/prep`

Next, create a new environment using your package and environment manager. Below shows how to, using `mamba`:

`.../prep % mamba create -n spider`

Next, activate the environment using:

`.../prep % mamba activate spider`

Next, install some necessary packages:

`.../prep % mamba install pip gdal`

Next, install the SPIDER requirements:

`.../prep % pip install -e .`

You should now have a fully functioning environment named `spider`. You can deactivate this for now and return to the top-level of the repository.
___
## 2 Preparing input data
> [!NOTE]
> Where `COUNTRY NAME` is used, make sure to replace it with the country name spelling that matches those used in the Natural Earth country boundaries shapfile (downloaded in step 2.1).

### 2.1 Input data
Before running the preparation scripts, some data must be downloaded and placed in the `data` folder. 

- The Global Oceans and Seas GeoPackage file can be downloaded from: https://www.marineregions.org/downloads.php
- The country boundaries shapefile can be downloaded from: https://www.naturalearthdata.com/downloads/50m-cultural-vectors/50m-admin-0-countries-2/
- OpenStreetMap Shapefile layers can be downloaded from (.shp.zip): https://download.geofabrik.de/
- The Corine Land Cover dataset (PROBAV_LC100_global_v3.0.1_2019-nrt_Discrete-Classification-map_EPSG-4326.tif) can be downloaded from: https://zenodo.org/records/3939050

Extra information:
- For the Global Oceans and Seas GeoPackage file, please place the downloaded `GOaS_v1_20211214_gpkg` folder into the `data` folder.
- For the OpenStreetMap files, please extract the contents from the downloaded folder into a subfolder as follows `data/OSM/[COUNTRY NAME]` for each country.
- For the files from Natural Earth Data, please place the downloaded `ne_50m_admin_0_countries` folder into the `data` folder.

>[!IMPORTANT]
>Ensure that the config file you are using, either `Country_config.yml` or `Country_config_hydro.yml`, located in the `inputs_spider` folder, contains all the details you want SPIDER to use. Any removal or addition of features will require modification of the Geo-X codebase.

### 2.2 Hydropower input data (optional)
If you want hydropower to be used as a generator, you will need another input file. It should be named `[COUNTRY NAME]_hydropower_plants.csv`. In the `data` folder, there is a template that can be filled in and name updated. That is where the file must be placed.

You can also use files from **open-source datasets** like the [Hydropower Database](https://github.com/energy-modelling-toolkit/hydro-power-database). You **must** rename the file to `[COUNTRY NAME]_hydropower_plants.csv` and ensure that the column titles match those in the template file. Extra columns do not need to be deleted, but they will not be taken into consideration when creating the GeoPackage file.

#### **Input Data Requirements**
- The script is designed for datasets containing:
  - **Latitude & Longitude** (plant location)
  - **Installed capacity (MW)**
  - **Annual generation (GWh)**
  - **Plant type** (e.g., HDAM, HPHS,...)
  - **Hydraulic head (m)**

## 3 Running data prep
There are two main scripts that are used, as well as the SPIDER submodule.

>[!IMPORTANT]
>The size of the country can affect the runs as follows:
> - The two main scripts may take more than 10 minutes to complete.
> - SPIDER may crash. This is due to insufficient or failing computer memory (RAM) and can be solved by increasing your RAM or running on another computer with sufficient RAM.

### 3.1 Run initial data prep before SPIDER
Activate the `prep` environment for this step.

There are some arguments that you need to pass via the terminal. They are:
- `countries`: (At least one required) This should be the names of the countries you are preparing with a space between them. Make sure that the spellings used for country names match those used in the Natural Earth country boundaries shapefile.
- `--hydro`: (Default is False) Only use this when you need to change to True.

Below is an example of what you could run (with `Country1` and `Country2` being specific country names):

`.../Geo-X-data-prep % python prep_before_spider.py Country1 Country2 --hydro True`

The above will first prepare a hydropower GeoPackage file, then pre-process the raw data, create a SPIDER config, and finally run GLAES. This will be done for each country provided.

### 3.2 Run SPIDER
>[!NOTE]
> Remember to deactivate the `prep` environment.

Now you will need to move to the `ccg-spider/prep` directory, activate the `spider` environment, and use the SPIDER CLI.

Take the following command, replace `Country` with the name of the country you are studying without spaces or periods, and paste it in your terminal:

`.../prep % gdal_rasterize data/Country.gpkg -burn 1 -tr 0.1 0.1 data/blank.tif && gdalwarp -t_srs EPSG:4088 data/blank.tif data/blank_proj.tif && spi --config=Country_config.yml Country_hex.geojson`

This command must be run for **each** country.
This will produce a set of hexagon tiles for each country using the parameters in the `Country_config.yml` file.

>[!IMPORTANT]
> Do not use multiple `&&` symbols to run more than one country at once. Only one set of `blank.tif` and `blank_proj.tif` files will be generated based on the first country, which will lead to inaccurate hexagon files for subsequent countries.

### 3.3 Run data prep after SPIDER
>[!NOTE]
> Remember to move back to the top-level of the repository and deactivate the `spider` environment.

Activate the `prep` environment for this step.

There are some arguments that you need to pass via the terminal. They are:
- `countries`: At least one required. This should be the name of the countries you are preparing with a space between them. Make sure that the spellings used for country names match those used in the Natural Earth country boundaries shapefile.
- `-ic`: At least one required. This is the two-letter ISO code for your countries. They must be in the same order as your countries.

Below is an example of what you could run (with `Country1` and `Country2` being specific country names, and `C1` and `C2` being specific 2-letter ISO Codes for each country respectively):

`.../Geo-X-data-prep % python prep_after_spider.py Country1 Country2 -ic C1 C2`

The above will combine the SPIDER and GLAES files. It will then assign an interest rate to different hexagons for different technology categories based on their country. Lastly, this script removes the duplicated hexagons that belong to a country which are not the desired country. 

The final file will be saved as `hex_final_[COUNTRY ISO CODE].geojson` for each country in the `inputs_geox/final_data` folder.

These `hex_final_[COUNTRY ISO CODE].geojson` files can be placed into a copy of the `Geo-X` repository in the `data` folder, as the baseline input data for modelling. 

If you set `hydro` to True, a `[COUNTRY NAME]_hydropower_dams.gpkg` file for each country will be generated into the `inputs_geox/final_data` folder. These files must be placed into the `data/hydro` folder of your `Geo-X` repository.

## Additional notes (Recommended to read at least once)
As the runs progress, you may not see all the files being generated, but rest assured they are there, taking up space. Once the runs are finished, it's recommended to save the necessary files and review the listed folders to delete any unnecessary files in order to free up space:
- `ccg-spider/prep`
- `ccg-spider/prep/data`
- `glaes/glaes/data`
- `inputs_geox/data`
- `inputs_glaes/processed`
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

