from multiprocessing import cpu_count
from common import *

# Define task
data_dir = "../images/"
blurry = "../blurry/"
pickles = "../pickles/"
duplicates = "../duplicates/"
histogram_dir = "../histogram_check/"
too_small = "../too_small/"

dirs = [data_dir, blurry, pickles, duplicates, histogram_dir, too_small]
for path in dirs:
    create_folder(path)

CPUs = cpu_count()
# It will be double, since downloading from both Bing and Flickr.
bing_data_num = 10000
flickr_data_num = 10000
ddg_data_num = 10000
topic = "notre dame cathedral aerial view"

print("""CURRENT CONFIGURATION:
	- CPUs = {}
	- Bing Images Number = {}
	- Flickr Images Number = {}
	- DuckDuckGo Images Number = {}
	- TOPIC = {}\n\n""".format(CPUs, bing_data_num, flickr_data_num, ddg_data_num, topic))

print("""OPTIONS:
	1. Download from Bing
	2. Download from Flickr
	3. Download from DuckDuckGo
	4. Rename JPEGs to JPG
	5. Fix all JPG, otherwise, remove
	6. Fix all PNG, otherwise, remove
	7. Convert all PNG to JPG
	8. Ensure minimum resolution
	9. Ensure over blurry image threshold
	10. Check for duplicates (image hashing)
	11. Histogram check (WIP)
	12. Image clustering (VGG16 and Birch)""")
