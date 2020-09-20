import imagehash
from glob import glob
from PIL import Image
from pprint import pprint
from tqdm import tqdm
import pickle
import os
import copyreg
import cv2
from chunks import chunks
import shutil


# Register Pickle behaviour for feature points.
def _pickle_keypoints(point):
    return cv2.KeyPoint, (*point.pt, point.size, point.angle,
                          point.response, point.octave, point.class_id)


def compute_img_hashes(image_folder, hash_file_path):
    imgs = glob(image_folder+"/*.*")

    # Compute or load hashes for each image.
    img_hash = {}
    if os.path.isfile(hash_file_path):
        img_hash = pickle.load(open(hash_file_path, "rb"))
    else:
        tq = tqdm(total=len(imgs))
        for img in imgs:
            _hash = imagehash.dhash(Image.open(img))
            img_hash[img] = _hash
            tq.update(1)
        pickle.dump(img_hash, open(hash_file_path, "wb"))


# Compute distance for each image.
def compute_hash_distance(img_dist_file, hash_file_path=None):
    imgs_d = {}
    if os.path.isfile(img_dist_file):
        imgs_d = pickle.load(open(img_dist_file, "rb"))
    else:
        img_hash = None
        if hash_file_path:
            img_hash = pickle.load(open(hash_file_path, "rb"))
        else:
            print("Hash file path not provided, cannot continue")

        tq = tqdm(total=len(imgs))
        for img in imgs:
            imgs_d[img] = {}
            hash1 = img_hash[img]
            for img2 in imgs:
                if img == img2:
                    continue
                hash2 = img_hash[img2]
                imgs_d[img][img2] = hash1 - hash2
            tq.update(1)
        pickle.dump(imgs_d, open(img_dist_file, "wb"))


def get_duplicate_images(img_dist_file, threshold=10):
    total_dup = []
    imgs_d = pickle.load(open(img_dist_file, "rb"))
    for img1 in imgs_d.keys():
        for img2 in imgs_d[img1].keys():
            dis = imgs_d[img1][img2]
            if dis == 0:
                total_dup.append((img1, img2))
            elif dis < threshold:
                print(img1, "-", img2, " = ", dis)

    return total_dup


def delete_duplicates(total_dup):
    # Remove the total duplicates
    for img1, img2 in total_dup:
        try:
            os.remove(img2)
        except:
            continue


def feature_extraction(image_folder, compare_folder, img_computed_data,
                       compare_computed_data, points_num=8192):
    # Get all images list.
    imgs = glob(image_folder+"/*.*")
    against = glob(compare_folder+"/*.*")

    # Register pickle handler for KeyPoints
    copyreg.pickle(cv2.KeyPoint().__class__, _pickle_keypoints)

    # Extract or load ORB features for all images.
    points_num = 8192
    orb = cv2.ORB_create(nfeatures=points_num)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    print("Preparing comparison set of images: ")
    compare_set = {}
    tq = tqdm(total=len(against))
    for item in against:
        fn = item.split("/")[-1].split(".")[-2]
        path = os.path.join(compare_computed_data, fn, ".orb")
        if os.path.isfile(path):
            compare_set[item] = pickle.load(open(path, "rb"))
            continue
        else:
            img = cv2.imread(item)
            kp, des = orb.detectAndCompute(img, None)
            compare_set[item] = {"kp": kp, "des": des}
            pickle.dump(compare_set[item], open(path, "wb"))
        tq.update()

    print("Preparing gathered set of images: ")
    match_set = {}
    tq = tqdm(total=len(imgs))
    for item in imgs:
        fn = item.split("/")[-1].split(".")[-2]
        path = os.path.join(img_computed_data, fn, ".orb")
        if os.path.isfile(path):
            match_set[item] = pickle.load(open(path, "rb"))
            continue
        else:
            img = cv2.imread(item)
            kp, des = orb.detectAndCompute(img, None)
            match_set[item] = {"kp": kp, "des": des}
            pickle.dump(match_set[item], open(path, "wb"))
        tq.update(1)


def match_features(img_computed_data, compare_computed_data, ratio_test=False, do_print=False):
    # Get pre-computed images list.
    imgs = glob(img_computed_data+"/*.*")
    against = glob(compare_computed_data+"/*.*")

    print("Loading compare set into memory: ")
    tq = tqdm(total=len(against))
    compare_set = {}
    for item in against:
        if os.path.isfile(item):
            compare_set[item] = pickle.load(open(path, "rb"))
        tq.update(1)

    print("Comparing images, each against entire test set: ")
    tq = tqdm(total=len(imgs))
    matches = {}
    for item in imgs:
        matches[item] = {}
        for key, val in compare_set.items():
            # If the same image, skip
            if item == key:
                continue

            # Read computed data.
            des1 = pickle.load(open(item, "rb"))["des"]  # Actual set image
            des2 = val["des"]  # Compare set image
            try:
                matches_data = bf.match(des1, des2)
            except Exception:
                matches_data = []

            if ratio_test:
                # Apply ratio test
                good = []
                for m,n in matches_data:
                    if m.distance < 0.75*n.distance:
                        #good.append([m])
                        good.append(True)
                matches[item][key] = len(good)
            else:
                # Those that don't exist in here probably don't have matches can be removed
                matches[item][key] = len(matches_data)

            tq.update(1)

    if do_print:
        pprint(matches)

    return matches


def total_matches(matches, do_print=False):
    totals = {}
    for key in matches.keys():
        totals[key] = 0
    for key, value in matches.items():
        for _, num_matches in value.items():
            totals[key] += num_matches

    if do_print:
        pprint(totals)
    return totals


def get_average_threshold(totals, do_print=False):
    val_list = list(totals.values())
    thr = sum(val_list)/len(val_list)
    if do_print:
        print("Threshold for valid image: ", thr)
    return thr


def get_threshold_items(totals, thr, max_res, do_print=False):
    actual_total = {}
    for key, val in totals.items():
        # Get resolution
        img = cv2.imread(key)
        height, width, _ = img.shape
        res = width * height

        # Scale thr
        thr = thr * (res / max_res)

        if val < thr:
            actual_total[key] = val

    if do_print:
        print("Total items under threshold:")
        pprint(actual_total)

    return actual_total


def move_threshold_items(totals, consider_folder, do_print=False):
    val_list = list(totals.values())

    l_max, l_min = max(val_list), min(val_list)
    base = l_min

    del(val_list)

    # 10 %
    percent_diff = (l_max - l_min)*.10

    for key, val in totals.items():
        # Check the difference between the last image and current image (num_features_matching)
        #diff_to_last = abs(last - val)

        # Update last image
        last = val
        # Check if difference bigger than the percent section of the set.
        if val > base and val-base > percent_diff:
            # If it is, update folder number
            f_num += 1
            base += percent_diff

        path = consider_folder+"L"+str(f_num)
        if not os.path.exists(path):
            os.makedirs(path)
        shutil.move(key, path)
