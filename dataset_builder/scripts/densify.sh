#!/bin/bash
cd openMVG

openMVG_main_ExportUndistortedImages -i output/sfm_data.bin -o undistorted --exportOnlyReconstructed 1 -n 24

openMVG_main_openMVG2openMVS -i output/sfm_data.bin -o ./export.mvs -d ./undistorted -n 24

mkdir dense_output

mv export.mvs undistorted dense_output

cd dense_output

/usr/local/bin/OpenMVS/DensifyPointCloud  -w ./