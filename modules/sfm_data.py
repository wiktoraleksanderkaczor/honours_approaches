from itertools import combinations
from fileio import copy, create_folder, filename
from multiprocessing import cpu_count
import rapidjson as json
from tqdm import tqdm
from glob import glob
import os


def merge_sfm_data(sfm_data_one, sfm_data_two, output):
    print("READING THE TWO FILES FOR MERGING")
    with open(sfm_data_one, "r") as infile:
        sfm_data1 = json.load(infile)

    with open(sfm_data_two, "r") as infile:
        sfm_data2 = json.load(infile)

    new = {
        "sfm_data_version": "0.3",
        "root_path": "openMVG/images",
        "views": sfm_data1["views"],
        "intrinsics": sfm_data1["intrinsics"],
        "extrinsics": sfm_data1["extrinsics"],
        "structure": sfm_data1["structure"],
        "control_points": []
    }

    view_ptr = new["views"][-1]["value"]["ptr_wrapper"]["id"]
    view_key_and_id_view_offset = new["views"][-1]["key"] + 1
    int_id_offset = new["intrinsics"][-1]["key"] + 1
    ext_id_offset = new["extrinsics"][-1]["key"] + 1
    print("ADDING SECOND VIEWS")
    for view in tqdm(sfm_data2["views"]):
        view["key"] += view_key_and_id_view_offset
        view_ptr += 1
        view["value"]["ptr_wrapper"]["id"] = view_ptr
        view["value"]["ptr_wrapper"]["data"]["id_view"] += view_key_and_id_view_offset
        if view["value"]["ptr_wrapper"]["data"]["id_intrinsic"] != 4294967295:
            view["value"]["ptr_wrapper"]["data"]["id_intrinsic"] += int_id_offset
        view["value"]["ptr_wrapper"]["data"]["id_pose"] += ext_id_offset
        new["views"].append(view)

    last_int_ptr = new["intrinsics"][-1]["value"]["ptr_wrapper"]["id"]
    print("ADDING SECOND INTRINSICS")
    for intrinsics in tqdm(sfm_data2["intrinsics"]):
        intrinsics["key"] += int_id_offset
        last_int_ptr += 1
        intrinsics["value"]["ptr_wrapper"]["id"] = last_int_ptr
        new["intrinsics"].append(intrinsics)

    print("ADDING SECOND EXTRINSICS")
    for extrinsics in tqdm(sfm_data2["extrinsics"]):
        extrinsics["key"] += ext_id_offset
        new["extrinsics"].append(extrinsics)

    highest_structure_id = sfm_data1["structure"][-1]["key"]
    print("ADDING SECOND STRUCTURE")
    for structure in tqdm(sfm_data2["structure"]):
        highest_structure_id += 1
        structure["key"] = highest_structure_id
        for observation in range(len(structure["value"]["observations"])):
            structure["value"]["observations"][observation]["key"] += view_key_and_id_view_offset

        new["structure"].append(structure)

    print("WRITING NEW FILE")
    with open(output, "w+") as outfile:
        json.dump(new, outfile, indent=4)


def merge_reconstructions(a=None, b=None):
    reconstructions = glob("reconstructions/*")
    options = list(combinations(reconstructions, 2))

    if not a or not b:
        option = None
        if options:
            while option not in range(-1, len(options)):
                for num, option in enumerate(options):
                    short = (
                        option[0].replace("reconstructions/", ""), 
                        option[1].replace("reconstructions/", "")
                    )
                    print(num, "-", short)
                print("-1 - EXIT DIALOG")
                try:
                    option = int(input())
                except:
                    option = None

        if option == -1:
            return

        a, b = options[option][0], options[option][1]

    # Conveniences
    merge_name = filename(a) + "~" + filename(b)
    merge_name = merge_name.replace(" ", "_")

    # Create folders for merging.
    create_folder("reconstructions/" + merge_name)
    create_folder("reconstructions/" + merge_name + "/openMVG/")
    create_folder("reconstructions/" + merge_name + "/openMVG/" + "data/")
    create_folder("reconstructions/" + merge_name +
                  "/openMVG/" + "localization_images/")
    create_folder("reconstructions/" + merge_name +
                  "/openMVG/" + "some_gps_localization/")
    create_folder("reconstructions/" + merge_name + "/openMVG/" + "output/")
    create_folder("reconstructions/" + merge_name + "/intermediate/")
    create_folder("reconstructions/" + merge_name + "/logs/")

    # Copy features and descriptors for one part of the pair
    features, descriptors = glob(
        a+"/openMVG/data/*.feat"), glob(a+"/openMVG/data/*.desc")

    for feature, descriptor in zip(features, descriptors):
        filename1 = filename(feature)
        filename2 = filename(descriptor)
        copy(feature, "reconstructions/" +
             merge_name + "/openMVG/data/" + filename1)
        copy(descriptor, "reconstructions/" +
             merge_name + "/openMVG/data/" + filename2)

    # Copy features and descriptors for the second part of the pair
    features, descriptors = glob(
        b+"/openMVG/data/*.feat"), glob(b+"/openMVG/data/*.desc")

    for feature, descriptor in zip(features, descriptors):
        filename1 = filename(feature)
        filename2 = filename(descriptor)
        copy(feature, "reconstructions/" +
             merge_name + "/openMVG/data/" + filename1)
        copy(descriptor, "reconstructions/" +
             merge_name + "/openMVG/data/" + filename2)

    copy(a+"/openMVG/data/image_describer.json", "reconstructions/" +
         merge_name + "/openMVG/data/image_describer.json")

    # Copy over the localisation images from both reconstructions.
    localisation_one = glob(a+"/openMVG/localization_images/*")
    localisation_two = glob(b+"/openMVG/localization_images/*")

    for img in localisation_one:
        copy(img, "reconstructions/" + merge_name +
             "/openMVG/localization_images/" + filename(img))

    for img in localisation_two:
        copy(img, "reconstructions/" + merge_name +
             "/openMVG/localization_images/" + filename(img))

    some_gps_one = glob(a+"/openMVG/some_gps_localization/*")
    some_gps_two = glob(b+"/openMVG/some_gps_localization/*")

    for img in some_gps_one:
        copy(img, "reconstructions/" + merge_name +
             "/openMVG/some_gps_localization/" + filename(img))

    for img in some_gps_two:
        copy(img, "reconstructions/" + merge_name +
             "/openMVG/some_gps_localization/" + filename(img))

    with open(a+"/intermediate/gps_data_from_images.json", "r") as infile:
        gps1 = json.load(infile)

    with open(b+"/intermediate/gps_data_from_images.json", "r") as infile:
        gps2 = json.load(infile)

    merged_gps = {}
    for key, val in gps1.items():
        merged_gps[key] = val
    for key, val in gps2.items():
        merged_gps[key] = val

    with open("reconstructions/" + merge_name + "/intermediate/gps_data_from_images.json", "w+") as outfile:
        json.dump(merged_gps, outfile, indent=4)

    with open(a+"/intermediate/some_gps_data_from_images.json", "r") as infile:
        gps1 = json.load(infile)

    with open(b+"/intermediate/some_gps_data_from_images.json", "r") as infile:
        gps2 = json.load(infile)

    merged_gps = {}
    for key, val in gps1.items():
        merged_gps[key] = val
    for key, val in gps2.items():
        merged_gps[key] = val

    with open("reconstructions/" + merge_name + "/intermediate/some_gps_data_from_images.json", "w+") as outfile:
        json.dump(merged_gps, outfile, indent=4)

    # Merge the actual "sfm_data".
    from sfm_data import merge_sfm_data
    merge_sfm_data(a+"/openMVG/output/sfm_data_geo.json",
                   b+"/openMVG/output/sfm_data_geo.json",
                   "reconstructions/" + merge_name + "/openMVG/output/sfm_data_geo.json")

    # Localise images in reconstruction and make relevant files.
    commands = [
        """
        openMVG_main_ConvertSfM_DataFormat \
            -i reconstructions/{}/openMVG/output/sfm_data_geo.json \
            -o reconstructions/{}/openMVG/output/sfm_data_geo.bin \
    """.format(merge_name, merge_name),

        """
        openMVG_main_ConvertSfM_DataFormat \
            -i reconstructions/{}/openMVG/output/sfm_data_geo.bin \
            -o reconstructions/{}/openMVG/output/sfm_data_geo.ply \
    """.format(merge_name, merge_name),

        """
    openMVG_main_SfM_Localization \
        -i reconstructions/{}/openMVG/output/sfm_data_geo.bin \
        --match_dir reconstructions/{}/openMVG/data \
        --out_dir reconstructions/{}/openMVG/localization_output \
        --query_image_dir reconstructions/{}/openMVG/localization_images \
        --numThreads {}
    """.format(merge_name, merge_name, merge_name, merge_name, cpu_count()),

        """
    openMVG_main_SfM_Localization \
        -i reconstructions/{}/openMVG/output/sfm_data_geo.bin \
        --match_dir reconstructions/{}/openMVG/data \
        --out_dir reconstructions/{}/openMVG/some_gps_localization_output \
        --query_image_dir reconstructions/{}/openMVG/some_gps_localization/ \
        --numThreads {}
    """.format(merge_name, merge_name, merge_name, merge_name, cpu_count())
    ]
    for cmd in commands:
        os.system(cmd)

    from gps import export_gps_to_file
    export_gps_to_file(
        georeference="reconstructions/" + merge_name +
        "/openMVG/output/sfm_data_geo.json",
        output="reconstructions/" + merge_name + "/openMVG/")
    export_gps_to_file(
        georeference="reconstructions/" + merge_name +
        "/openMVG/localization_output/sfm_data_expanded.json",
        output="reconstructions/" + merge_name + "/openMVG/")
    export_gps_to_file(
        georeference="reconstructions/" + merge_name +
        "/openMVG/some_gps_localization_output/sfm_data_expanded.json",
        output="reconstructions/" + merge_name + "/openMVG/some_gps_localization_output/")

    with open(a + "/logs/images_for_georeferencing.json", "r") as infile:
        used_for_geo1 = json.load(infile)

    with open(b + "/logs/images_for_georeferencing.json", "r") as infile:
        used_for_geo2 = json.load(infile)

    with open("reconstructions/" + merge_name + "/logs/images_for_georeferencing.json", "w+") as outfile:
        merged_used_for_geo = used_for_geo1 + used_for_geo2
        json.dump(merged_used_for_geo, outfile, indent=4)

    from gps import get_accuracy
    get_accuracy("reconstructions/" + merge_name + "/intermediate/gps_data_from_images.json",
                 "reconstructions/" + merge_name + "/openMVG/sfm_data_geo_positions.json",
                 "reconstructions/" + merge_name + "/openMVG/sfm_data_expanded_positions.json",
                 output="reconstructions/" + merge_name + "/openMVG/localised_accuracy.json",
                 georeferencing="reconstructions/" + merge_name + "/logs/images_for_georeferencing.json")

    get_accuracy("reconstructions/" + merge_name + "/intermediate/some_gps_data_from_images.json",
                 "reconstructions/" + merge_name + "/openMVG/sfm_data_geo_positions.json",
                 "reconstructions/" + merge_name +
                 "/openMVG/some_gps_localization_output/sfm_data_expanded_positions.json",
                 output="reconstructions/" + merge_name + "/openMVG/some_gps_localised_accuracy.json",
                 georeferencing="reconstructions/" + merge_name + "/logs/images_for_georeferencing.json")

    from gps import convert_to_kml
    convert_to_kml(georeference="reconstructions/" + merge_name + "/openMVG/sfm_data_expanded_positions.json",
                   output="reconstructions/" + merge_name + "/openMVG/positions.kml")

    # Compare accuracy of localisation between reconstructions.
    acc1 = a + "/openMVG/localised_accuracy.json"
    acc2 = b + "/openMVG/localised_accuracy.json"
    acc1 = json.load(open(acc1, "r"))
    acc2 = json.load(open(acc2, "r"))
    new_acc = json.load(
        open("reconstructions/" + merge_name + "/openMVG/localised_accuracy.json", "r"))
    acc_changes = {}
    for img in new_acc.keys():
        difference_accuracy = None
        if img != "sum_error":
            if img in acc1.keys():
                difference_accuracy = acc1[img]["metres_distance_from_actual"] - \
                    new_acc[img]["metres_distance_from_actual"]
            if img in acc2.keys():
                difference_accuracy = acc2[img]["metres_distance_from_actual"] - \
                    new_acc[img]["metres_distance_from_actual"]
            if difference_accuracy:
                acc_changes[img] = difference_accuracy

    acc_changes["sum"] = sum(acc_changes.values())

    json.dump(acc_changes, open("reconstructions/" + merge_name +
              "/accuracy_changes_from_merge.json", "w+"), indent=4)


# https://gitlab.com/educelab/sfm-utils/-/blob/develop/sfm_utils/openmvg.py
def remove_images_from_reconstruction(sfm_data, images_to_remove):
    with open(sfm_data, "r") as infile:
        data = json.load(infile)

    # Get all valid views (not in image to remove) and remove poses for images to remove.
    invalid_pose_ids = [view["value"]["ptr_wrapper"]["data"]["id_pose"]
                        for view in data["views"] if view["value"]["ptr_wrapper"]["data"]["filename"] in images_to_remove]
    data["extrinsics"] = [pose for pose in data["extrinsics"]
                          if pose["key"] not in invalid_pose_ids]
    valid_view_ids = [view["value"]["ptr_wrapper"]
                      ["data"]["id_view"] for view in data["views"]]

    # Removing structures referencing those removed views.
    for structure in data["structure"]:
        for observation in structure["value"]["observations"]:
            if observation["key"] not in valid_view_ids:
                structure["value"]["observations"].remove(observation)

    # find a point has fewer than 2 views and remove them
    data["structure"][:] = [data["structure"][i] for i in range(0, len(
        data["structure"])) if len(data["structure"][i]["value"]["observations"]) >= 2]

    with open(sfm_data, "w+") as outfile:
        json.dump(data, outfile, indent=4)
