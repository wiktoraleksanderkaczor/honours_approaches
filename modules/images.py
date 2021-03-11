from glob import glob
from tqdm import tqdm
import cv2
from joblib import Parallel, delayed
from imagehash import dhash, hex_to_hash
from pathlib import Path
from PIL import Image
import json
import os
from fileio import filename, move


def check_task(image, hashes, RESOLUTION_THRESHOLD, BLURRINESS_THRESHOLD, under_res, too_blurry):
    if image not in hashes:
        img = cv2.imread(image, cv2.IMREAD_GRAYSCALE)

        # Find image size in pixels, if too low, move to under resolution folder.
        height, width = img.shape
        val = width * height
        if val < RESOLUTION_THRESHOLD:
            move(image, under_res + filename(image))
            return

        # Find blurriness value, if too high, move to blurry folder.
        val = cv2.Laplacian(img, cv2.CV_64F).var()
        if val < BLURRINESS_THRESHOLD:
            move(image, too_blurry + filename(image))
            return

        # Hash image.
        hashes[image] = str(dhash(Image.open(image)))


def check_images(path, under_res, too_blurry, RESOLUTION_THRESHOLD=307200, BLURRINESS_THRESHOLD=125):
    print("CHECKING IMAGES FOR UNDER RESOLUTION, BLURRINESS, AND IF PASSED, HASHING:")
    if os.path.isfile("logs/hashes.json"):
        with open("logs/hashes.json", "r") as infile:
            hashes = json.load(infile)
    else:
        hashes = {}

    images = glob(path+"*.jpg", recursive=True)
    Parallel(n_jobs=24, prefer="threads")(
        delayed(check_task)(image, hashes, RESOLUTION_THRESHOLD, BLURRINESS_THRESHOLD, under_res, too_blurry) for image in tqdm(images)
    )

    # Save all hashes.
    with open("logs/hashes.json", "w+") as outfile:
        json.dump(hashes, outfile, indent=4)


def get_duplicate_images(path, duplicate, threshold=5):
    print("CALCULATING SIZE FOR EACH IMAGE FILE")
    sizes = {}
    images = glob(path+"*.jpg", recursive=True)
    for image in images:
        sizes[image] = Path(image).stat().st_size

    print("COMPUTING CLOSE IMAGES:")
    files = glob(path+"*.jpg", recursive=True)
    with open("logs/hashes.json", "r") as infile:
        hashes = json.load(infile)

    for key, hash in hashes.items():
        hashes[key] = hex_to_hash(hash)

    close = []
    from copy import deepcopy
    comparison = deepcopy(files)
    for image1 in tqdm(files):
        comparison = {path: hashes[path] - hashes[image1]
                      for path in comparison if path != image1}
        for image2, result in comparison.items():
            if result <= threshold:
                try:
                    # Chose the one with the smaller size to be moved.
                    if sizes[image1] > sizes[image2]:
                        if image2 not in close:
                            close.append(image2)
                    else:
                        if image1 not in close:
                            close.append(image1)

                except FileNotFoundError:
                    # The offending file was likely moved in a previous pair
                    continue
        comparison.pop(image1, None)

    print("MOVING FOUND ITEMS TO 'duplicates' FOLDER")
    for image in close:
        move(image, duplicate + filename(image))

    return close


def images_rename(path):
    files = glob(path+"*.*", recursive=True)
    for image in files:
        split = image.split(".")
        fname = split[-2]
        ext = split[-1]
        if ext == "jpeg":
            move(image, fname+".jpg")


def find_initial_image_pair(threshold=100, nfeatures=8192):
    orb = cv2.ORB_create(nfeatures=nfeatures)
    des_for_img = {}
    with open("logs/images_for_georeferencing.json", "r") as infile:
        images = json.load(infile)
    
    print("EXTRACTING FEATURES:")    
    for image in tqdm(images):
        img = cv2.imread(image)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        kp, des = orb.detectAndCompute(img, None)
        des_for_img[image] = des

    num_matches = {}
    index_params= dict(algorithm=6,  # FLANN_INDEX_LSH
                    table_number = 12, # 12
                    key_size = 20,     # 20
                    multi_probe_level = 2) #2    
    # Higher numbers for the above give more precision, take more time. 
    # 100 was the recommended higher precision number on the OpenCV page.
    search_params = dict(checks=100)   # or pass empty dictionary
    flann = cv2.FlannBasedMatcher(index_params,search_params)

    print("MATCHING IMAGES:")
    for img1, des1 in tqdm(des_for_img.items()):
        for img2, des2 in des_for_img.items():
            if img1 != img2:
                sorted_key = repr(sorted((img1, img2)))
                if sorted_key not in num_matches.keys():
                    matches = flann.knnMatch(des1, des2, k=2)

                    good = []
                    for item in matches:
                        if len(item) == 2:
                            m,n = item
                            if m.distance < 0.75*n.distance:
                                good.append([m])

                    num_matches[sorted_key] = len(good)
    
    good_matches = []
    for key, val in num_matches.items():
        if val > threshold:
            good_matches.append((eval(key), val))
        
    return good_matches