#!/bin/bash
cd openMVG

nice -n 20 openMVG_main_SfM_Localization -i output/sfm_data_geo.bin --match_dir data --out_dir localization_output --query_image_dir localization_images/ --numThreads 24
