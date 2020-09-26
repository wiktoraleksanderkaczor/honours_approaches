import imagehash
from glob import glob
from PIL import Image
from pprint import pprint
from tqdm import tqdm
import pickle
import os
import fnmatch
import copyreg
import cv2
from chunks import chunks
import shutil
import concurrent.futures


# Register Pickle behaviour for feature points.
def _pickle_keypoints(point):
    return cv2.KeyPoint, (*point.pt, point.size, point.angle,
                          point.response, point.octave, point.class_id)


def hash_thread(img, img_hash, tq):
    if img not in img_hash.keys():  
        _hash = imagehash.dhash(Image.open(img))
        img_hash[img] = _hash
    tq.update(1)


def compute_img_hashes(image_folder, hash_file_path):
    imgs = glob(image_folder+"/*.*")

    # Compute or load hashes for each image.
    img_hash = {}
    if os.path.isfile(hash_file_path):
        img_hash = pickle.load(open(hash_file_path, "rb"))

    tq = tqdm(total=len(imgs))
    WORKERS = 4
    chunks_list = list(chunks(imgs, WORKERS))
    for chunk in chunks_list:
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
            for img in chunk:
                executor.submit(hash_thread, img, img_hash, tq)
    """
    for img in imgs:
        if img not in img_hash:  
            _hash = imagehash.dhash(Image.open(img))
            img_hash[img] = _hash
        tq.update(1)
    """
    pickle.dump(img_hash, open(hash_file_path, "wb"))

def hash_dist(img, imgs, img_hash, imgs_d, tq):
    if img not in imgs_d:
        imgs_d[img] = {}
        hash1 = img_hash[img]
        for img2 in imgs:
            if not img == img2 and img2 not in imgs_d[img]:
                try:
                    hash2 = img_hash[img2]
                    imgs_d[img][img2] = hash1 - hash2
                except Exception as e:
                    print(e)
    tq.update(1)


# Compute distance for each image.
def compute_hash_distance(image_folder, img_dist_file, hash_file_path=None):
    imgs = glob(image_folder+"/*.*")
    imgs_d = {}

    if os.path.isfile(img_dist_file):
        imgs_d = pickle.load(open(img_dist_file, "rb"))

    img_hash = None
    if os.path.isfile(hash_file_path):
        img_hash = pickle.load(open(hash_file_path, "rb"))
    else:
        print("Hash file path not provided, cannot continue")

    tq = tqdm(total=len(imgs))
    WORKERS = 4
    chunks_list = list(chunks(imgs, WORKERS))
    for chunk in chunks_list:
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
            for img in chunk:
                executor.submit(hash_dist, img, imgs, img_hash, imgs_d, tq)

    pickle.dump(imgs_d, open(img_dist_file, "wb"))


def get_duplicate_images(img_dist_file, threshold=10, print_close=False):
    total_dup = []
    imgs_d = pickle.load(open(img_dist_file, "rb"))
    tq = tqdm(total=len(imgs_d))
    for img1 in imgs_d.keys():
        for img2 in imgs_d[img1].keys():
            dis = imgs_d[img1][img2]
            if dis == 0:
                total_dup.append((img1, img2))
            elif dis < threshold:
                if print_close:
                    print(img1, "-", img2, " = ", dis)
        tq.update(1)

    return total_dup


def delete_duplicates(total_dup):
    # Remove the total duplicates
    for _, img2 in total_dup:
        try:
            os.remove(img2)
        except:
            continue


def extract_thread(item, detector, dst_path, tq):
    fn = item.split("/")[-1].split(".")[-2]
    path = os.path.join(dst_path, fn+".pts")
    if not os.path.isfile(path):
        img = cv2.imread(item)
        kp, des = detector.detectAndCompute(img, None)
        data = {"kp": kp, "des": des}
        pickle.dump(data, open(path, "wb"))
    tq.update(1)


def feature_extraction(image_folder, compare_folder, img_computed_data,
                       compare_computed_data, feature_matcher="ORB", points_num=8192):
    # Get all images list.
    imgs = glob(image_folder+"/*.*")
    against = glob(compare_folder+"/*.*")

    # Number of worker threads
    WORKERS = 4

    # Register pickle handler for KeyPoints
    copyreg.pickle(cv2.KeyPoint().__class__, _pickle_keypoints)

    detector = None
    if feature_matcher == "SIFT":
        detector = cv2.SIFT(nfeatures=points_num)
    elif feature_matcher == "SURF":
        detector = cv2.SURF(nfeatures=points_num)
    elif feature_matcher == "ORB":
        detector = cv2.ORB_create(nfeatures=points_num)

    print("Preparing comparison set of images: ")
    tq = tqdm(total=len(against))
    """
    # SINGLE_THREADED:
    for item in against:
        fn = item.split("/")[-1].split(".")[-2]
        path = os.path.join(compare_computed_data, fn+".pts")
        if not os.path.isfile(path):
            img = cv2.imread(item)
            kp, des = detector.detectAndCompute(img, None)
            data = {"kp": kp, "des": des}
            pickle.dump(data, open(path, "wb"))
        tq.update(1)
    """
    # MULTI_THREADED:
    chunks_list = chunks(against, WORKERS)
    for chunk in chunks_list:
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
            for item in chunk:
                executor.submit(extract_thread, item, detector, compare_computed_data, tq)

    print("Preparing gathered set of images: ")
    tq = tqdm(total=len(imgs))
    """
    # SINGLE_THREADED:
    for item in imgs:
        fn = item.split("/")[-1].split(".")[-2]
        path = os.path.join(img_computed_data, fn+".pts")
        if not os.path.isfile(path):
            img = cv2.imread(item)
            kp, des = detector.detectAndCompute(img, None)
            data = {"kp": kp, "des": des}
            pickle.dump(data, open(path, "wb"))
        tq.update(1)
    """
    # MULTI_THREADED:
    chunks_list = chunks(imgs, WORKERS)
    for chunk in chunks_list:
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
            for item in chunk:
                executor.submit(extract_thread, item, detector, img_computed_data, tq)

def get_matcher(feature_matcher="ORB", bf_or_flann="BF"):
    #https://www.programcreek.com/python/?code=NetEase%2Fairtest%2Fairtest-master%2Fairtest%2Ftrash%2Ffind_obj.py
    matcher, norm = None, None
    if feature_matcher == "ORB":
        norm = cv2.NORM_HAMMING
    elif feature_matcher in ["SIFT", "SURF"]:
        norm = cv2.NORM_L2
    if bf_or_flann == "FLANN":
        if norm == cv2.NORM_L2:
            FLANN_INDEX_KDTREE = 1
            flann_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
        else:
            FLANN_INDEX_LSH = 6
            flann_params= dict(algorithm = FLANN_INDEX_LSH,
                                table_number = 6, # 12
                                key_size = 12,     # 20
                                multi_probe_level = 1) #2
        matcher = cv2.FlannBasedMatcher(flann_params, {})
        # bug : need to pass empty dict (#1329)
    elif bf_or_flann == "BF":
        matcher = cv2.BFMatcher(norm)
    else:
        matcher = cv2.BFMatcher(norm)

    return matcher

def match_features_compare(compare_computed_data, compute_cache, matcher, ratio_test=False, do_print=False):
    print("Computing correct threshold for valid images:")
    imgs = glob(compare_computed_data+"/*.*")

    print("Loading compare set into memory: ")
    tq = tqdm(total=len(imgs))
    compare_set = {}
    for item in imgs:
        if os.path.isfile(item):
            compare_set[item] = pickle.load(open(item, "rb"))
        tq.update(1)

    print("Computing threshold:")
    tq = tqdm(total=len(compare_set)*len(compare_set))
    matches = {}
    if os.path.isfile(compute_cache):
        matches = pickle.load(open(compute_cache, "rb"))
    for key1, val1 in compare_set.items():
        if key1 not in matches.keys():
            matches[key1] = {}
            for key2, val2 in compare_set.items():
                # If the same image, skip
                if key1 == key2:
                    continue

                # If it was in the cache file, skip
                if key2 in matches[key1].keys():
                    continue

                # Read computed data.
                des1 = val1["des"]  # Actual set image
                des2 = val2["des"]  # Compare set image
                try:
                    matches_data = matcher.knnMatch(des1, des2, k=2)
                except Exception:
                    matches_data = []

                if ratio_test:
                    # Apply ratio test
                    good = []
                    for m, n in matches_data:
                        if m.distance < 0.75*n.distance:
                                #good.append([m])
                                good.append(True)
                    matches[key1][key2] = len(good)
                else:
                    # Those that don't exist in here probably don't have matches can be removed
                    matches[key1][key2] = len(matches_data)

                tq.update(1)

    pickle.dump(matches, open(compute_cache, "wb"))

    return matches

def match_features(img_computed_data, compare_computed_data, compute_cache, matcher, ratio_test=False, do_print=False):
    # Get pre-computed images list.
    imgs = glob(img_computed_data+"/*.*")
    against = glob(compare_computed_data+"/*.*")

    print("Loading compare set into memory: ")
    tq = tqdm(total=len(against))
    compare_set = {}
    for item in against:
        if os.path.isfile(item):
            compare_set[item] = pickle.load(open(item, "rb"))
        tq.update(1)

    print("Comparing images, each against entire test set: ")
    tq = tqdm(total=len(imgs)*len(compare_set))
    matches = {}
    if os.path.isfile(compute_cache):
        matches = pickle.load(open(compute_cache, "rb"))
    for item in imgs:
        if item not in matches.keys():
            matches[item] = {}
        for key, val in compare_set.items():
            # If the same image, skip
            if item == key:
                continue

            # If it was in the cache file, skip
            if key in matches[item].keys():
                continue

            # Read computed data.
            des1 = pickle.load(open(item, "rb"))["des"]  # Actual set image
            des2 = val["des"]  # Compare set image
            try:
                matches_data = matcher.knnMatch(des1, des2, k=2)
            except Exception:
                matches_data = []

            if ratio_test:
                # Apply ratio test
                good = []
                for m, n in matches_data:
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

    pickle.dump(matches, open(compute_cache, "wb"))

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


def find(pattern, walk_data):
    result = []
    for root, files in walk_data:
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result[0]


def get_threshold_items(totals, thr, max_res, img_folder, get_scaled_thr_only=False, do_print=False):
    below_thr = {}
    over_thr = {}

    avg_val = sum(list(totals.values()))/len(totals)

    walk_data = []
    for root, _, files in os.walk(img_folder):
        walk_data.append((root, files))

    tq = tqdm(total=len(totals))
    for key, val in totals.items():
        # Get image file path from pts_data filename
        fn = key.split(".")[-2].split("/")[-1]
        if fn == "3252121974_cfe79e0010_o":
            exec("")
        img_path = find(fn+".*", walk_data)

        # Get resolution
        img = cv2.imread(img_path)
        height, width, _ = img.shape
        res = width * height

        # Scale thr
        ratio = 1 - ((avg_val / thr) + (res / max_res) / 2) 
        #ratio = (val / thr)
        img_thr = None
        if ratio < 1:
            img_thr = thr * ratio
        else:
            img_thr = thr
        
        img_thr = abs(img_thr)

        if not get_scaled_thr_only:
            if val < img_thr:
                below_thr[img_path] = val
            else:
                over_thr[img_path] = val
        else:
            over_thr[img_path] = img_thr

        tq.update(1)

    if do_print:
        pprint(below_thr)
        print("Total items under threshold: ", len(below_thr))
        pprint(over_thr)
        print("Total items over threshold: ", len(over_thr))

    return below_thr, over_thr


def move_threshold_items(totals, consider_folder, do_print=False):
    """
    val_list = list(totals.values())

    l_max, l_min = max(val_list), min(val_list)
    base = l_min

    del(val_list)

    # 10 %
    percent_diff = (l_max - l_min)*.10
    """
    for key, val in totals.items():
        """
        # Check the difference between the last image and current image (num_features_matching)
        diff_to_last = abs(last - val)

        # Update last image
        last = val
        """
        """
        # Check if difference bigger than the percent section of the set.
        if val > base and val-base > percent_diff:
            # If it is, update folder number
            f_num += 1
            base += percent_diff

        path = os.path.join(consider_folder,"L"+str(f_num))
        if not os.path.exists(path):
            os.makedirs(path)
        shutil.move(key, path)
        """
        shutil.move(key, consider_folder)


if __name__ == "__main__":
    import download
    download.runner()