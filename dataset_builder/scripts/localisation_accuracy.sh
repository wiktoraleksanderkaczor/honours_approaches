#!/bin/bash
cd openMVG

# Get positions from georegistered reconstruction.
python get_gps_from_json.py output/sfm_data_geo.json

# Get positions from georegistered reconstruction plus newly localised images.
python get_gps_from_json.py localization_output/sfm_data_expanded.json