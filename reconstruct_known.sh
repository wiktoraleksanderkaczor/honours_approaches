#!/bin/bash
cd openMVG

# To reconstruct again, from known localized poses 
mkdir from_known_poses
openMVG_main_ComputeStructureFromKnownPoses -i output/sfm_data.json -m data -o form_known_poses/from_known_poses -d -f data/matches.f.bin