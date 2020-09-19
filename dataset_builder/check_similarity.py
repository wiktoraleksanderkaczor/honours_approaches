import imagehash
import glob
from PIL import Image
from pprint import pprint
from tqdm import tqdm
import pickle
import os
import sys
import subprocess
import copyreg
import cv2

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# Register Pickle behaviour for feature points.
def _pickle_keypoints(point):
    return cv2.KeyPoint, (*point.pt, point.size, point.angle,
                          point.response, point.octave, point.class_id)
copyreg.pickle(cv2.KeyPoint().__class__, _pickle_keypoints)

imgs = glob.glob("./dataset_builder/images_grey/*.*")

# Compute or load hashes for each image.
img_hash = {}
if os.path.isfile('./dataset_builder/hashes.p'):
    img_hash = pickle.load(open("./dataset_builder/hashes.p", "rb"))
else:
    tq = tqdm(total=len(imgs))
    for img in imgs:
        _hash = imagehash.dhash(Image.open(img))
        img_hash[img] = _hash
        tq.update(1)
    pickle.dump(img_hash, open("./dataset_builder/hashes.p", "wb"))

# Compute distance for each image.
imgs_d = {}
if os.path.isfile('./dataset_builder/imgs_d.p'):
    img_hash = pickle.load(open("./dataset_builder/imgs_d.p", "rb"))
else:
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
    pickle.dump(img_hash, open("./dataset_builder/imgs_d.p", "wb"))


threshold = 10
total_dup = []
for img1 in imgs_d.keys():
    for img2 in imgs_d[img1].keys():
        dis = imgs_d[img1][img2]
        if dis == 0:
            total_dup.append((img1, img2))
        elif dis < threshold:
            print(img1, "-", img2, " = ", dis)

#pprint(total_dup)
#print("Length \"total_dup\": ", len(total_dup))
#There were 188, before first delete, backup of original in "copy" folder.

# Remove the total duplicates
for img1, img2 in total_dup:
    try:
        os.remove(img2)
    except:
        continue

del(total_dup)
del(imgs_d)
del(img_hash)

# Get all images after delete action.
imgs = glob.glob("./dataset_builder/images_grey/*.*")

# Create list of blocks of five with step one, file paths.
sift_check = []
#neighbours = 250
neighbours = len(imgs)
start, end, length = 0, 0 + neighbours, len(imgs)

sift_check = list(chunks(imgs, neighbours))

#pprint(sift_check)

# Extract or load SIFT features for all images.
points_num = 8192
sift = cv2.SIFT_create(nfeatures=points_num)
orb = cv2.ORB_create()

bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

total = 0
for i in range(len(sift_check)):
    total += len(sift_check[i]) * len(sift_check[i]) 

matches = {}
tq = tqdm(total=total)

for num, files in enumerate(sift_check):
    batch_match = {}
    for fi1 in files:
        fn = fi1.split("/")[-1].split(".")[-2]
        path = "./dataset_builder/sift_data/"+fn+".sift"
        if os.path.isfile(path):
            batch_match[fi1] = pickle.load(open(path, "rb"))
            continue
        else:
            img = cv2.imread(fi1)

            kp, des = orb.detectAndCompute(img,None)
            
            batch_match[fi1] = {"kp": kp, "des": des}

            pickle.dump(batch_match[fi1], open(path, "wb"))

    for fi1 in files:
        matches[fi1] = {}
        for fi2 in files:
            tq.update(1)
            # If the same image in chunk, skip
            if fi1 == fi2:
                continue

            # Check if image 1 was already matched against the second image.
            # If so, add matches count and skip
            for key in matches.keys():
                try:
                    if fi1 in matches[fi2].keys():
                        matches[fi1][fi2] = matches[fi2][fi1]
                        continue
                except Exception:
                    continue

            #Read image into numpy array.
            des1 = batch_match[fi1]["des"]
            des2 = batch_match[fi2]["des"]
            try:
                matches_data = bf.match(des1,des2)
            except Exception:
                matches_data = []
            """
            # Apply ratio test
            good = []
            for m,n in matches_data:
                if m.distance < 0.75*n.distance:
                    #good.append([m])
                    good.append(True)
            """

            # Those that don't exist in here probably don't have matches can be removed
            matches[fi1][fi2] = len(matches_data)

    # Update counter.
    #print(num, "/", total)

# Now I get the feeling lower resolution images will be penalised because of less features to be found in their less pixels...
# Maybe I can scale the judgement based on number of pixels?
pprint(matches)

totals = {}
for key in matches.keys():
    totals[key] = 0
for key, value in matches.items():
    for key1, val1 in value.items():
        totals[key] += val1

tmp = []
for key, val in totals.items():
    tmp.append(val)

thr = sum(tmp)/len(tmp)
pprint(totals)
actual_total = {}
for key, val in totals.items():
    if val < thr:
        actual_total[key] = val

tmp = []
for key, val in totals.items():
    tmp.append(val)

import operator
sorted_d = sorted(actual_total.items(), key=operator.itemgetter(1))
pprint(sorted_d)
print("Threshold for valid image: ", thr)
input("Press any key to continue...")

l_max, l_min = max(tmp), min(tmp)
base = l_min
# 10 %
dif = (l_max - l_min)*.10
import shutil
# I might want to make those equal sized groups too, except for when the difference between one item and the next is too great, some threshold.
# This threshold could be 1% of the difference? There could be many more groups too.
# Those should be percentages, for the difference between the max and min of what remains.
for key, val in actual_total.items():
    # Check the difference between the last image and current image (num_features_matching)
    diff = last - val
    # Update last image
    last = val
    # Check if difference bigger than the percent section of the set.
    if val > base and val-base > dif:
        # If it is, update folder number
        f_num += 1
        base += dif

    path = "./dataset_builder/to_consider/L"+str(f_num)
    if not os.path.exists(path):
        os.makedirs(path)
    shutil.move(key, path)
