#!/bin/bash
cd openMVG

openMVG_main_SfMInit_ImageListing -i images -d ../sensor_database.txt -o init #--use_pose_prior 1

openMVG_main_ComputeFeatures -i init/sfm_data.json -o data --describerMethod SIFT --describerPreset NORMAL --numThreads 24

openMVG_main_ComputeMatches -i init/sfm_data.json -o data/ --guided_matching 1