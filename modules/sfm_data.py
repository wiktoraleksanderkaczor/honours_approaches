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
                    print(num, "-", option)
                print("-1 - EXIT DIALOG")
                try:
                    option = int(input())
                except:
                    option = None
        
        if option == -1:
            return

        a, b = options[option][0], options[option][1]

    # Conveniences
    merge_name = filename(a)+ "~" +filename(b)
    merge_name = merge_name.replace(" ", "_")

    # Create folders for merging.
    create_folder("reconstructions/" + merge_name)
    create_folder("reconstructions/" + merge_name + "/openMVG/")
    create_folder("reconstructions/" + merge_name + "/openMVG/" + "data/")
    create_folder("reconstructions/" + merge_name + "/openMVG/" + "localization_images/")
    create_folder("reconstructions/" + merge_name + "/openMVG/" + "output/")
    create_folder("reconstructions/" + merge_name + "/intermediate/")

    # Copy features and descriptors for one part of the pair
    features, descriptors = glob(a+"/openMVG/data/*.feat"), glob(a+"/openMVG/data/*.desc")

    for feature, descriptor in zip(features, descriptors):
        filename1 = filename(feature)
        filename2 = filename(descriptor)
        copy(feature, "reconstructions/" + merge_name + "/openMVG/data/" + filename1)
        copy(descriptor, "reconstructions/" + merge_name + "/openMVG/data/" + filename2)

    
    # Copy features and descriptors for the second part of the pair
    features, descriptors = glob(b+"/openMVG/data/*.feat"), glob(b+"/openMVG/data/*.desc")

    for feature, descriptor in zip(features, descriptors):
        filename1 = filename(feature)
        filename2 = filename(descriptor)
        copy(feature, "reconstructions/" + merge_name + "/openMVG/data/" + filename1)
        copy(descriptor, "reconstructions/" + merge_name + "/openMVG/data/" + filename2)

    copy(a+"/openMVG/data/image_describer.json", "reconstructions/" + merge_name + "/openMVG/data/image_describer.json")

    # Copy over the localisation images from both reconstructions.
    localisation_one = glob(a+"/openMVG/localization_images/*")
    localisation_two = glob(b+"/openMVG/localization_images/*")

    for img in localisation_one:
        copy(img, "reconstructions/" + merge_name + "/openMVG/localization_images/" + filename(img))

    for img in localisation_two:
        copy(img, "reconstructions/" + merge_name + "/openMVG/localization_images/" + filename(img))

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

    # Merge the actual "sfm_data".
    from sfm_data import merge_sfm_data
    merge_sfm_data(a+"/openMVG/output/sfm_data_geo.json", \
        b+"/openMVG/output/sfm_data_geo.json", \
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
    """.format(merge_name, merge_name, merge_name, merge_name, cpu_count())
    ]
    for cmd in commands:
        os.system(cmd)

    from gps import export_gps_to_file
    export_gps_to_file(
        georeference="reconstructions/" + merge_name + "/openMVG/output/sfm_data_geo.json", \
        output="reconstructions/" + merge_name + "/openMVG/")
    export_gps_to_file(
        georeference="reconstructions/" + merge_name + "/openMVG/localization_output/sfm_data_expanded.json", \
        output="reconstructions/" + merge_name + "/openMVG/")

    with open(a + "/logs/not_used_for_georeferencing.json", "r") as infile:
        not_used_for_geo1 = json.load(infile)

    with open(b + "/logs/not_used_for_georeferencing.json", "r") as infile:
        not_used_for_geo2 = json.load(infile)

    with open("reconstructions/" + merge_name + "/logs/not_used_for_georeferencing.json") as outfile:
        merged_not_used_for_geo = not_used_for_geo1 + not_used_for_geo2
        json.dump(merged_not_used_for_geo, outfile, indent=4)


    from gps import get_accuracy
    get_accuracy("reconstructions/" + merge_name + "/intermediate/gps_data_from_images.json",
                    "reconstructions/" + merge_name + "/openMVG/sfm_data_geo_positions.json",
                    "reconstructions/" + merge_name + "/openMVG/sfm_data_expanded_positions.json",
                    output="reconstructions/" + merge_name + "/localised_accuracy.json"
                    "reconstructions/" + merge_name + "/logs/not_used_for_georeferencing.json")

    from gps import convert_to_kml
    convert_to_kml(georeference="reconstructions/" + merge_name + "/openMVG/sfm_data_expanded_positions.json", \
        output="reconstructions/" + merge_name + "/openMVG/positions.kml")

    # Compare accuracy of localisation between reconstructions.
    acc1 = a + "/openMVG/localised_accuracy.json"
    acc2 = b + "/openMVG/localised_accuracy.json"
    acc1 = json.load(open(acc1, "r"))
    acc2 = json.load(open(acc2, "r"))
    new_acc = json.load(open("reconstructions/" + merge_name + "/localised_accuracy.json", "r"))
    acc_changes = {}
    for img in new_acc.keys():
        difference_accuracy = None
        if img in acc1.keys():
            difference_accuracy = acc1[img]["metres_distance_from_actual"] - new_acc[img]["metres_distance_from_actual"]
        if img in acc2.keys():
            difference_accuracy = acc2[img]["metres_distance_from_actual"] - new_acc[img]["metres_distance_from_actual"]
        if difference_accuracy:
            acc_changes[img] = difference_accuracy

    json.dump(acc_changes, open("reconstructions/" + merge_name + "/accuracy_changes_from_merge.json", "w+"), indent=4)

def get_bad_altitude_before_georeferencing(gps_data_from_images, sfm_data, threshold=15):
    with open(sfm_data, "r") as infile:
        data = json.load(infile)
    with open(gps_data_from_images, "r") as infile:
        gps_data = json.load(infile)

    # Check if distances between gps data and position in reconstruction are directly proportional, if so, likely to be correct.
    # Else, remove from reconstruction's "sfm_data"... and the reconstruction files.  
    # Add to log of "removed because wrong altitude"

    # Get the pose for each image, if it exists.
    pose_for_image = {}
    for view in data["views"]:
        img_data = view["value"]["ptr_wrapper"]["data"] 
        if img_data["filename"] in gps_data.keys():
            pose_id = img_data["id_pose"]
            for extrinsic in data["extrinsics"]:
                if extrinsic["key"] == pose_id:
                    pose_for_image[img_data["filename"]] = extrinsic["value"]["center"]

    # If image has pose in reconstruction.
    gps_data = {img: data for img, data in gps_data.items() if img in pose_for_image.keys()}

    # Euclidean distance
    # https://stackoverflow.com/questions/1401712/how-can-the-euclidean-distance-be-calculated-with-numpy
    from scipy.spatial import distance
    bad_position = []
    #proportions = {}
    num_images = len(gps_data.keys())
    for img1, gps1 in gps_data.items():
        relative_sum = 0
        gps_sum = 0
        for img2, gps2 in gps_data.items():
            if img1 != img2:
                pose1 = pose_for_image[img1]
                pose2 = pose_for_image[img2]
                relative1 = (pose1[0], pose1[1], pose1[2])
                relative2 = (pose2[0], pose2[1], pose2[2])
                gps_pose1 = (gps1["lat"], gps1["lon"], gps1["alt"])
                gps_pose2 = (gps2["lat"], gps2["lon"], gps2["alt"])
                gps_distance = distance.euclidean(gps_pose1, gps_pose2)
                relative_distance = distance.euclidean(relative1, relative2)
                gps_sum += gps_distance
                relative_sum += relative_distance
        
        relative_sum = relative_sum / num_images
        gps_sum = gps_sum / num_images
        proportion = gps_sum * relative_sum
        if proportion > threshold:
            bad_position.append(img1)
        #proportions[img1] = proportion

    #proportions["average"] = sum(proportions.values()) / len(proportions.keys())

    return bad_position

def remove_images_from_reconstruction(sfm_data, images_to_remove):
    # If ran without any images to remove, it generates error on converting to '.bin' using openMVG;
    # """
    # Error while trying to deserialize a polymorphic pointer. Could not find type id 1
    # The input SfM_Data file "openMVG/output/sfm_data.json" cannot be read.
    # """
    if images_to_remove:
        with open(sfm_data, "r") as infile:
            data = json.load(infile)

        remove = []
        for view in data["views"]:
            img_data = view["value"]["ptr_wrapper"]["data"] 
            if img_data["filename"] in images_to_remove:
                if view not in remove:
                    remove.append(view)

        data["views"] = [view for view in data["views"] if view not in remove]

        # Extrinsics removal depends on views, and views on extrinsics, the rest depend on views
        data = remove_unused_views(data)
        data = remove_unused_intrinsics(data)
        data = remove_unused_extrinsics(data)
        data = remove_unused_structures(data)
        data = clean_up_order(data)

        with open(sfm_data, "w+") as outfile:
            json.dump(data, outfile, indent=4)


def remove_unused_views(sfm_data_json):
    # Remove if it view doesn't have a reconstructed pose.
    remove = []
    pose_keys = [extrinsic["key"] for extrinsic in sfm_data_json["extrinsics"]]
    for view in sfm_data_json["views"]:
        if view["value"]["ptr_wrapper"]["data"]["id_pose"] not in pose_keys:
            remove.append(view)
    
    sfm_data_json["views"] = [view for view in sfm_data_json["views"] if view not in remove]
    return sfm_data_json

def remove_unused_intrinsics(sfm_data_json):
    # Remove if extrinsics aren't featured in views.
    remove = []
    view_intrinsic_keys = [view["value"]["ptr_wrapper"]["data"]["id_intrinsic"] for view in sfm_data_json["views"]]
    for intrinsic in sfm_data_json["intrinsics"]:
        if intrinsic["key"] not in view_intrinsic_keys:
            if intrinsic not in remove:
                remove.append(intrinsic)
    
    sfm_data_json["intrinsics"] = [intrinsic for intrinsic in sfm_data_json["intrinsics"] if intrinsic not in remove]
    return sfm_data_json


def remove_unused_extrinsics(sfm_data_json):
    # Remove if extrinsics aren't featured in views.
    remove = []
    view_pose_keys = [view["value"]["ptr_wrapper"]["data"]["id_pose"] for view in sfm_data_json["views"]]
    for extrinsic in sfm_data_json["extrinsics"]:
        if extrinsic["key"] not in view_pose_keys:
            if extrinsic not in remove:
                remove.append(extrinsic)
    
    sfm_data_json["extrinsics"] = [extrinsic for extrinsic in sfm_data_json["extrinsics"] if extrinsic not in remove]
    return sfm_data_json


def remove_unused_structures(sfm_data_json):
    view_keys = [view["key"] for view in sfm_data_json["views"]]
    for structure in sfm_data_json["structure"]:
        remove = []
        for observation in structure["value"]["observations"]:
            if observation["key"] not in view_keys:
                if observation not in remove:
                    remove.append(observation)

        if remove:
            structure["value"]["observations"] = [observation for observation in structure["value"]["observations"] if observation not in remove]
    
    # find a point has fewer than 2 views and remove them
    sfm_data_json["structure"][:] = [sfm_data_json["structure"][i] for i in range(0,len(sfm_data_json["structure"])) if len(sfm_data_json["structure"][i]["value"]["observations"]) >= 2]
    return sfm_data_json


def clean_up_order(sfm_data_json):
    # Get the mapping
    filename_to_ids = {}
    for view in sfm_data_json["views"]:
        filename = view["value"]["ptr_wrapper"]["data"]["filename"]
        id_view = view["value"]["ptr_wrapper"]["data"]["id_view"]
        id_intrinsic = view["value"]["ptr_wrapper"]["data"]["id_intrinsic"]
        id_pose =  view["value"]["ptr_wrapper"]["data"]["id_pose"]
        filename_to_ids[filename] = {"id_view": id_view, "id_intrinsic": id_intrinsic, "id_pose": id_pose}

    from copy import deepcopy
    filename_to_ids = deepcopy(filename_to_ids)

    # Change intrinsics order, save in "filename_to_ids"
    for counter, intrinsic in zip(range(len(sfm_data_json["intrinsics"])), sfm_data_json["intrinsics"]):
        if intrinsic["key"] != counter:
            for _, value in filename_to_ids.items():
                if value["id_intrinsic"] == intrinsic["key"]:
                    value["id_intrinsic"] = counter
            intrinsic["key"] = counter

    # Change extrinsics order, save in "filename_to_ids"
    for counter, extrinsic in zip(range(len(sfm_data_json["extrinsics"])), sfm_data_json["extrinsics"]):
        if extrinsic["key"] != counter:
            for _, value in filename_to_ids.items():
                if value["id_pose"] == extrinsic["key"]:
                    value["id_pose"] = counter
            extrinsic["key"] = counter

    # Change views order and "id_view" using "filename_to_ids", save mapping from old id to new id in "old_to_new"
    old_to_new_view_id = {}
    counter = 0
    for counter, view in zip(range(len(sfm_data_json["views"])), sfm_data_json["views"]):
        old_to_new_view_id[view["key"]] = counter
        if view["key"] != counter:
            filename = view["value"]["ptr_wrapper"]["data"]["filename"]
            view["key"] = counter
            view["value"]["ptr_wrapper"]["data"]["id_view"] = counter
            view["value"]["ptr_wrapper"]["data"]["id_intrinsic"] = filename_to_ids[filename]["id_intrinsic"]
            view["value"]["ptr_wrapper"]["data"]["id_pose"] = filename_to_ids[filename]["id_pose"]

    sfm_data_json = remove_unused_intrinsics(sfm_data_json)

    # Change structure mapping, using "old_to_new"
    for structure in sfm_data_json["structure"]:
        for observation in structure["value"]["observations"]:
            observation["key"] = old_to_new_view_id[observation["key"]]
    return sfm_data_json

