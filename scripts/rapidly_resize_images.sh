#!/bin/bash
# This is to reduce the dataset to something usable for manipulation.
find ../tf_data/ -name '*.jpg' -execdir mogrify -resize 256x256! {} \;
