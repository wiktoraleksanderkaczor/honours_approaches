import os
import re
import cv2
from undist_function import undist_function

dist_folder = 'folder_to_save_undistorted_images/'
if not os.path.exists(dist_folder):
    os.makedirs(dist_folder)

lines = open("./results/results.txt", "r").readlines()
paths, focal, distortion = [], [], []

for line in lines:
    vals = re.split(r'\t+', line)
    print("path:", vals[0])
    paths.append(vals[0])
    print("focal:",vals[2])
    focal.append(vals[2])
    print("distortion:",vals[4])
    distortion.append(vals[4])


for item in range(len(paths)):
    distorted_img = cv2.imread(paths[item])
    img_h, img_w, _ = distorted_img.shape

    xi = distortion[item]
    f = focal[item]
    f_dist = (img_w / img_h) * (img_h / 299) # Focal length
    u0_dist = img_w / 2
    v0_dist = img_h / 2

    img = undist_function(img_h, img_w, f_dist, xi, distorted_img)

    cv2.imwrite(dist_folder+paths[item], img)
