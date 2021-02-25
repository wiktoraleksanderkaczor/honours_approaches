#!/bin/bash
cd openMVG

openMVG_main_geodesy_registration_to_gps_position -i output/sfm_data.bin -o output/sfm_data_geo.bin

openMVG_main_ConvertSfM_DataFormat -i output/sfm_data_geo.bin -o output/sfm_data_geo.json

openMVG_main_ConvertSfM_DataFormat -i output/sfm_data_geo.bin -o output/sfm_data_geo_cloudcompare_viewable.ply