#!/bin/bash
cd openMVG

openMVG_main_IncrementalSfM -i init/sfm_data.json -m data -o output --prior_usage 0 -a image-1d44f4881333c778c5b3394c86e2d104.jpg -b image-2f1672f0092a0f3a47199db65bf5ded2.jpg
