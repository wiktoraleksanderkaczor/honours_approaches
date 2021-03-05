#!/bin/bash
cd openMVG

# Get positions from georegistered reconstruction.
#echo "ONLY GEOREGISTERED RECONSTRUCTION"
python get_gps_from_json.py output/sfm_data_geo.json

# Get positions from georegistered reconstruction plus newly localised images.
#echo "GEOREGISTERED RECONSTRUCTION PLUS LOCALISED IMAGES"
python get_gps_from_json.py localization_output/sfm_data_expanded.json

python check_accuracy_from_gps.py