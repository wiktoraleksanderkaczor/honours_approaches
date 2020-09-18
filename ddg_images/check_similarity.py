import imagehash
import glob
from PIL import Image
from pprint import pprint
from tqdm import tqdm
import pickle
import os
import pandas as pd
pd.set_option("display.max_rows", None, "display.max_columns", None)

import cv2

imgs = glob.glob("./ddg_images/images_grey/*.*")

# Compute or load hashes for each image.
img_hash = {}
if os.path.isfile('./ddg_images/hashes.p'):
    img_hash = pickle.load(open("./ddg_images/hashes.p", "rb"))
else:
    tq = tqdm(total=len(imgs))
    for img in imgs:
        _hash = imagehash.dhash(Image.open(img))
        img_hash[img] = _hash
        tq.update(1)
    pickle.dump(img_hash, open("./ddg_images/hashes.p", "wb"))

# Compute distance for each image.
imgs_d = {}
if os.path.isfile('./ddg_images/imgs_d.p'):
    img_hash = pickle.load(open("./ddg_images/imgs_d.p", "rb"))
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
    pickle.dump(img_hash, open("./ddg_images/imgs_d.p", "wb"))


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
imgs = glob.glob("./ddg_images/images_grey/*.*")

# Create list of blocks of five with step one, file paths.
sift_check = []
neighbours = 3
start, end, length = 0, 0 + neighbours, len(imgs)

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

sift_check = list(chunks(imgs, neighbours))

#pprint(sift_check)


# Extract or load SIFT features for all images.
#import sift_pyocl as sift
#from pysift import computeKeypointsAndDescriptors as sift_image
points_num = 2048
sift = cv2.SIFT_create(nfeatures=points_num)
orb = cv2.ORB_create()

bf = cv2.BFMatcher()

total = len(sift_check)
matches = {}

tq = tqdm(total=total*neighbours*neighbours)

for num, files in enumerate(sift_check):
    batch_match = {}
    for fi1 in files:
        fn = fi1.split("/")[-1].split(".")[-2]
        path = "./ddg_images/sift_data/"+fn+".sift"
        if os.path.isfile(path):
            batch_match[fi1] = pickle.load(open(path, "rb"))
            continue
        else:
            img = cv2.imread(fi1)
            #kp, des = sift.detectAndCompute(img,None)
            _, des = orb.detectAndCompute(img,None)
            
            #batch_match[fi1] = {"kp": None, "des": des}
            batch_match[fi1] = {"des": des}

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
            matches_data = bf.knnMatch(des1,des2, k=2)

            # Apply ratio test
            good = []
            for m,n in matches_data:
                if m.distance < 0.75*n.distance:
                    #good.append([m])
                    good.append(True)

            # Those that don't exist in here probably don't have matches can be removed
            matches[fi1][fi2] = len(good)

    # Update counter.
    #print(num, "/", total)

pprint(matches)

totals = {}
for key in matches.keys():
    totals[key] = 0
for key, value in matches.items():
    for key1, val1 in value.items():
        totals[key] += val1

pprint(totals)
exec("")
