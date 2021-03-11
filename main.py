import sys
sys.path.append("./modules")

from config import *
from fileio import copy, filename
from pprint import pprint
from multiprocessing import cpu_count
import os
import json
import glob

LOCATION = \
    """
CURRENT LOCATION IS (if untrue, exit):
	Address: {}
	Latitude and Longitude: {}, {}
	https://www.google.com/maps/@{},{},17.5z
""".format(location.address, location.latitude,
           location.longitude, location.latitude,
           location.longitude)

MENU = \
    """
OPTIONS (Recommended steps ordered will be in [N] format):
	1. Download from Flickr [1]
	2. Fix image by renaming JPEGs to JPG, converting PNGs, and running "jpeginfo". [2]
	3. Ensure minimum resolution, image over blurry threshold and no duplicates in set [3]
	4. Get GPS data, verify, segregate, make a cleared version and save the good data in JSON. [4]
	5. Copy some GPS images, most cleared GPS images, and fill with largest normal images to openMVG folder. [5]
	6. OpenMVG Feature Detection and Matching [11]
	7. Find best initial pair and use OpenMVG to reconstruct [12]
	8. OpenMVG Georegister Model [13]
	9. OpenMVG Attempt to localise "cleared_gps" minus images used for georeferencing in reconstruction. [14]
	10. Get localisation attempt accuracy from reconstruction. [15]
	11. Reconstructed locations to KML file
	-1. EXIT
"""


def handle_choice(choice):
    if choice == 1:
        from download import links_from_flickr, download
        links = links_from_flickr(TOPIC)
        download(links, "intermediate/images/")

    elif choice == 2:
        from images import images_rename
        images_rename("intermediate/images/")

        commands = [
            # Convert PNGs to JPGs.
            """mogrify -format jpg {}*.png;""".format(
                "intermediate/images/"),

            # Remove PNG duplicates
            """rm {}/*.png;""".format("intermediate/images/"),

            # Check for faulty JPGs, if so, remove.
            """jpeginfo -cd {}*.jpg;""".format("intermediate/images/")
        ]
        for cmd in commands:
            os.system(cmd)

    elif choice == 3:
        from images import check_images, get_duplicate_images
        check_images("intermediate/images/", "intermediate/too_small/", "intermediate/too_blurry/",
                     RESOLUTION_THRESHOLD=PIXEL_NUM_THRESHOLD, BLURRINESS_THRESHOLD=BLURRINESS_THRESHOLD)

        close_images = get_duplicate_images(
            "intermediate/images/", "intermediate/duplicates/", threshold=CLOSE_IMAGE_THRESHOLD)
        print("IMAGES CLOSE BY HASH:")
        pprint(close_images)

    elif choice == 4:
        from gps import get_gps
        get_gps("intermediate/images/",
                "intermediate/some_gps/",
                "intermediate/good_gps/",
                "intermediate/bad_gps/",
                location,
                METRES_THR=METRES_RADIUS_THRESHOLD)
        from gps import remove_exif
        remove_exif("intermediate/good_gps/",
                    "intermediate/cleared_gps/")

    elif choice == 5:
        from gps import select_and_copy_GPS_images
        select_and_copy_GPS_images("intermediate/images/",
                                   "intermediate/cleared_gps/",
                                   "intermediate/good_gps/",
                                   NUM_GPS_IMAGES,
                                   NUM_LARGEST_IMAGES,
                                   "openMVG/images/")

    elif choice == 6:
        commands = [
            """
			openMVG_main_SfMInit_ImageListing \
				-i openMVG/images \
				-d sensor_database.txt \
				-o openMVG/init
			""",

            """
			openMVG_main_ComputeFeatures \
				-i openMVG/init/sfm_data.json \
				-o openMVG/data \
				--describerMethod SIFT \
				--describerPreset NORMAL \
				-f 1 \
                --numThreads {}
			""".format(cpu_count()),

            """
			openMVG_main_ComputeMatches \
				-i openMVG/init/sfm_data.json \
				-o openMVG/data/ \
				--guided_matching 1 \
                -f 1
			"""
        ]
        for cmd in commands:
            os.system(cmd)

    elif choice == 7:
        from images import find_initial_image_pair
        num_matches = find_initial_image_pair()
        for num, match in enumerate(num_matches):
            print(num, match[0])
        
        choice = None
        while choice not in range(len(num_matches)):
            choice = int(input("ENTER YOUR CHOICE OF INITIALISATION PAIR: "))
        a, b = num_matches[choice][0][0], num_matches[choice][0][1]
        a, b = filename(a), filename(b)
        print("PAIR SELECTED: ", a, b)

        cmd = \
            """openMVG_main_IncrementalSfM \
			-i openMVG/init/sfm_data.json \
			-m openMVG/data \
			-o openMVG/output \
			--prior_usage 0 \
            --initialPairA {} \
            --initialPairB {}
		""".format(a, b)
        os.system(cmd)

    elif choice == 8:
        commands = [
            """
            openMVG_main_geodesy_registration_to_gps_position \
				-i openMVG/output/sfm_data.bin \
				-o openMVG/output/sfm_data_geo.bin
            """,

            """
            openMVG_main_ConvertSfM_DataFormat \
				-i openMVG/output/sfm_data_geo.bin \
				-o openMVG/output/sfm_data_geo.json
            """,

            """
            openMVG_main_ConvertSfM_DataFormat \
				-i openMVG/output/sfm_data_geo.bin \
				-o openMVG/output/sfm_data_geo_cloudcompare_viewable.ply
            """
        ]
        for cmd in commands:
            os.system(cmd)

    elif choice == 9:
        localisation_images = glob("intermediate/good_gps/*.jpg")

        with open("logs/images_for_georeferencing.json", "r") as infile:
            used_for_georeferencing = json.load(infile)

        for image in localisation_images:
            if image not in used_for_georeferencing:
                copy(image, "openMVG/localisation_images/" + filename(image))

        cmd = \
            """
		openMVG_main_SfM_Localization \
			-i openMVG/output/sfm_data_geo.bin \
			--match_dir openMVG/data \
			--out_dir openMVG/localization_output \
			--query_image_dir openMVG/localization_images \
			--numThreads {}
		""".format(cpu_count())

        os.system(cmd)

    elif choice == 10:
        from gps import export_gps_to_file
        export_gps_to_file(georeference="openMVG/output/sfm_data_geo.json")
        export_gps_to_file(
            georeference="openMVG/localization_output/sfm_data_expanded.json")

        from gps import get_accuracy
        get_accuracy("intermediate/gps_data_from_images.json",
                     "openMVG/sfm_data_geo_positions.json",
                     "openMVG/sfm_data_expanded_positions.json")

    elif choice == 11:
        from gps import convert_to_kml
        convert_to_kml(georeference="openMVG/sfm_data_geo_positions.json")

    elif choice == -1:
        exit(0)


def main(execute=None):
    if not execute:
        print(LOCATION)
        while True:
            try:
                choice = int(input(MENU))
            except:
                choice = 0
            handle_choice(choice)
    else:
        for choice in execute:
            handle_choice(choice)


if __name__ == "__main__":
    main()
