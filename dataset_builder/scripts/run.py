from multiprocessing import cpu_count
import subprocess
from common import *

# Define task
data_dir = "intermediate/images/"
blurry = "intermediate/blurry/"
pickles = "intermediate/pickles/"
duplicates = "intermediate/duplicates/"
histogram_dir = "intermediate/histogram_check/"
too_small = "intermediate/too_small/"
bad_gps = "intermediate/bad_gps/"

dirs = [data_dir, blurry, pickles, duplicates, histogram_dir, too_small, bad_gps]
for path in dirs:
    create_folder(path)

CPUs = cpu_count()
# It will be double, since downloading from both Bing and Flickr.
bing_data_num = 100
flickr_data_num = 100
ddg_data_num = 100
topic = "notre dame cathedral"
pwd = os.getcwd()

print("""CURRENT CONFIGURATION:
	- CPUs = {}
	- Bing Images Number = {}
	- Flickr Images Number = {}
	- DuckDuckGo Images Number = {}
	- TOPIC = {}
	- Present Working Directory = {}\n\n""".format(CPUs, \
		bing_data_num, flickr_data_num, ddg_data_num, topic, pwd))

def display_menu():
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
	12. Image clustering (VGG16 and Birch)
	13. Generate "image_list.txt"
	14. Get GPS data and verify
	15. EXIT""")
	
# Plus 1 for index
valid_choices = list(range(1, 15 + 1, 1))

while True:
	display_menu()
	choice = input()
	choice = int(choice)
	while choice not in valid_choices:
		print("That was not a valid choice, try again: ")
		choice = input()
		choice = int(choice)
	
	if choice == 1:
		from links_bing import links_from_bing
		links = links_from_bing(topic, bing_data_num)
		download(links, data_dir, service="bing")
	
	elif choice == 2:
		from links_flickr import links_from_flickr
		links = links_from_flickr(topic, flickr_data_num)
		download(links, data_dir, service="flickr")
	
	elif choice == 3:
		from links_ddg import links_from_ddg
		links = links_from_ddg(topic, ddg_data_num)
		download(links, data_dir, service="ddg")
	
	elif choice == 4:
		from rename_jpegs import images_rename
		images_rename(data_dir)
	
	elif choice == 5:
		cmd = r"""cd {}; jpeginfo -cd {}*.jpg;""".format(pwd, data_dir)
		os.system(cmd)
	
	elif choice == 6:
		cmd = r"""cd {}; pngcheck -fq {}*.png | cut -d " " -f2 | xargs rm;""".format(pwd, data_dir)
		os.system(cmd)
	
	elif choice == 7:
		# Convert to JPGs
		cmd = r"""cd {}; mogrify -format jpg {}*.png;""".format(pwd, data_dir)
		os.system(cmd)

		# Remove PNG duplicates
		cmd = "cd {}; rm {}/*.png;".format(pwd, data_dir)
		os.system(cmd)
	
	elif choice == 8:
		from check_resolution import get_under_res
		under_res = get_under_res(data_dir)
		print("Under resolution items:")
		pprint(under_res)
		print("Moving found items..")
		if not move_to(under_res, too_small):
			del(under_res)

	elif choice == 9:
		#https://www.pyimagesearch.com/2015/09/07/blur-detection-with-opencv/
		# A constant of 200, it does pretty good!
		from check_blur import get_too_blurry
		too_blurry_data = get_too_blurry(data_dir, 125)

		if not move_to(too_blurry_data, blurry):
			del(too_blurry_data)
		
	elif choice == 10:
		from image_hashing import compute_img_hashes, compute_hash_distance, get_duplicate_images
		compute_img_hashes(data_dir)
		compute_hash_distance(data_dir)
		data_dup, data_close = get_duplicate_images(data_dir, threshold=5)

		print("Data duplicates:")
		pprint(data_dup)
		print("Length of data duplicates: ", len(data_dup))

		if not move_to(data_dup, duplicates):
			del(data_dup)
	
	elif choice == 11:
		from histogram_check import check_histogram
		data_to_move = check_histogram(data_dir)

		print("Moving {} images...".format(len(data_to_move)))
		if not move_to(data_to_move, histogram_dir):
			del(data_to_move)
		
	elif choice == 12:
		n_clusters = -1
		while not isinstance(n_clusters, int) or n_clusters <= 0:
			n_clusters = input("How many clusters? ")
			try:
				n_clusters = int(n_clusters)
			except:
				n_clusters = -1

		from image_clustering import create_cluster_folders, cluster
		create_cluster_folders(n_clusters, path="output/")
		cluster(data_dir, n_clusters)

	elif choice == 13:
		from generate_image_list import generate_image_list
		generate_image_list(data_dir)

	elif choice == 14:
		from gps_image import get_gps
		#gps_num, cartesian = get_gps
		get_gps(data_dir)
		
	elif choice == 15:
		exit(0)

