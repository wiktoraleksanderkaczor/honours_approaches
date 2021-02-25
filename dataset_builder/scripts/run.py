#!/home/badfox/miniconda3/bin/python
from multiprocessing import cpu_count
import subprocess
from common import *

# Define task
intermediate = "./intermediate/"
data_dir = intermediate+"images/"
blurry = intermediate+"blurry/"
pickles = intermediate+"pickles/"
duplicates = intermediate+"duplicates/"
histogram_dir = intermediate+"histogram_check/"
too_small = intermediate+"too_small/"
bad_gps = intermediate+"bad_gps/"
good_gps = intermediate+"good_gps/"
cleared_gps = intermediate+"cleared_gps/"
openMVG = "./openMVG/"
openMVG_images = openMVG+"images/"
logs = "./logs/"

dirs = [data_dir, blurry, pickles, duplicates, \
	histogram_dir, too_small, bad_gps, good_gps, \
	cleared_gps, logs, openMVG_images]

for path in dirs:
    create_folder(path)

CPUs = cpu_count()
# It will be double, since downloading from both Bing and Flickr.
bing_data_num = 1500
flickr_data_num = 5000
ddg_data_num = 1500
topic = "Notre Dame Cathedral France"
pwd = os.getcwd()

NUM_LARGEST_IMAGES = 500
NUM_GPS_IMAGES = 30

print("""CURRENT CONFIGURATION:
	- CPUs = {}
	- Bing Images Number = {}
	- Flickr Images Number = {}
	- DuckDuckGo Images Number = {}
	- TOPIC = {}
	- Present Working Directory = {}\n\n""".format(CPUs, \
		bing_data_num, flickr_data_num, ddg_data_num, topic, pwd))

def display_menu():
	print("""OPTIONS (Recommended steps ordered will be in [N] format):
	1. Download from Bing [1]
	2. Download from Flickr [2]
 	3. Download from DuckDuckGo [3]
	4. Rename JPEGs to JPG [4]
	5. Convert all PNG to JPG [5]
	6. Fix all JPG, otherwise, remove [6]
	7. Ensure minimum resolution [7]
	8. Ensure over blurry image threshold [8]
	9. Check for duplicates (image hashing) [9]
	10. Get GPS data, verify, segregate, and save the good data in JSON. [10]
	11. Remove EXIF data from all but N images. [11]
	12. Move N GPS images and the cleared GPS image (minus the ten GPS images) to "openMVG/images" folder. [12]
	13. OpenMVG Reconstruct [13]
	14. OpenMVG Reconstruct (from known poses, second reconstruction)
	15. OpenMVG Georegister Model [14]
	16. OpenMVG Attempt to localise all "images" and "cleared_gps" in reconstruction. [15]
	17. Get Localisation attempt accuracy from reconstruction. [16]
	18. OpenMVS Densify Point Cloud (just for visualisation)
	0. EXIT""")
	
# Plus 1 for index
valid_choices = list(range(0, 18 + 1, 1))

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
		# Convert to JPGs
		cmd = r"""cd {}; mogrify -format jpg {}*.png;""".format(pwd, data_dir)
		os.system(cmd)

		# Remove PNG duplicates
		cmd = "cd {}; rm {}/*.png;".format(pwd, data_dir)
		os.system(cmd)
	
	elif choice == 6:
		cmd = r"""cd {}; jpeginfo -cd {}*.jpg;""".format(pwd, data_dir)
		os.system(cmd)
	
	elif choice == 7:
		from check_resolution import get_under_res
		under_res = get_under_res(data_dir)
		print("Under resolution items:")
		pprint(under_res)
		print("Moving found items..")
		if not move_to(under_res, too_small):
			del(under_res)

	elif choice == 8:
		#https://www.pyimagesearch.com/2015/09/07/blur-detection-with-opencv/
		# A constant of 200, it does pretty good!
		from check_blur import get_too_blurry
		too_blurry_data = get_too_blurry(data_dir, 125)

		if not move_to(too_blurry_data, blurry):
			del(too_blurry_data)
		
	elif choice == 9:
		from image_hashing import compute_img_hashes, compute_hash_distance, get_duplicate_images
		compute_img_hashes(data_dir)
		compute_hash_distance(data_dir)
		data_dup, data_close = get_duplicate_images(data_dir, threshold=5)

		print("Data duplicates:")
		pprint(data_dup)
		print("Length of data duplicates: ", len(data_dup))

		if not move_to(data_dup, duplicates):
			del(data_dup)

	elif choice == 10:
		from gps_image import get_gps
		get_gps(data_dir, good_gps, bad_gps)
		
	elif choice == 11:
		from gps_image import remove_exif
		remove_exif(good_gps, cleared_gps)

	elif choice == 12:
		gps_images = glob.glob(good_gps+"*.jpg")
		no_gps_images = glob.glob(cleared_gps+"*.jpg")
		try:
			ten_gps_images = random.sample(gps_images, NUM_GPS_IMAGES)
			to_take = [] + ten_gps_images
			for image in no_gps_images:
				if image.split("/")[-1] not in ten_gps_images:
					to_take.append(image)

			images = glob.glob(data_dir+"*.jpg")
			img_and_size = {}
			for image in images:
				img_and_size[image] = os.path.getsize(image)
			
			NUM_LARGEST_IMAGES -= len(to_take)
			sorted_by_size = sorted(img_and_size.items(), key=lambda x: x[1], reverse=True)
			if len(sorted_by_size) >= NUM_LARGEST_IMAGES:
				for item in sorted_by_size[:NUM_LARGEST_IMAGES]:
					img, size = item
					to_take.append(img)
			else:
				for item in sorted_by_size:
					img, size = item
					to_take.append(img)

			for image in tqdm(to_take):
				shutil.copyfile(image, openMVG_images+image.split("/")[-1])
		except Exception as e:
			print("Failed to select or copy image to \"openMVG/images\" folder due to;", e)
		
	elif choice == 13:
		os.system("bash reconstruct.sh")

	elif choice == 14:
		os.system("bash reconstruct_known.sh")

	elif choice == 15:
		os.system("bash georegister.sh")

	elif choice == 16:
		os.system("bash localise.sh")

	elif choice == 17:
		try:
			shutil.copyfile(intermediate+"gps_data_from_images.json", openMVG+"gps_data_from_images.json")
		except Exception as e:
			print("Failed to copy gps_data_from_images.json due to;", e)
		
		try:
			shutil.copyfile("./get_gps_from_json.py", openMVG+"get_gps_from_json.py")
		except Exception as e:
			print("Failed to copy openMVG location extraction script due to;", e)

		try:
			shutil.copyfile("./check_accuracy_from_gps.py", openMVG+"check_accuracy_from_gps.py")
		except Exception as e:
			print("Failed to copy openMVG location accuracy checking script due to;", e)

		os.system("bash localisation_accuracy.sh")

	elif choice == 18:
		os.system("bash densify.sh")

	elif choice == 0:
		exit(0)

