#!/bin/bash
cd openMVG

mkdir localization_images

cp ../intermediate/images/* localization_images

cp ../intermediate/cleared_gps/* localization_images

openMVG_main_SfM_Localization -i output/sfm_data_geo.bin --match_dir data --out_dir localization_output --query_image_dir localization_images/ --numThreads 24
