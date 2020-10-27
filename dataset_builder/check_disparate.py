import glob
from PIL.Image import open as open_img
from imagehash import dhash
from tqdm import tqdm
import multiprocessing
import concurrent.futures
from pprint import pprint

def hash(path):
    return dhash(open_img(path))

files = glob.glob("compare_set/*")

hashes = {}
for fi in tqdm(files):
    hashes[fi] = hash(fi)

distances = {}
for fi in tqdm(files):
    item = sum([hashes[fi]-j for j in hashes.values()])
    distances[fi] = item

increasing = sorted(distances, key=distances.get)

import shutil

most_disparate = 50
for item in increasing[-most_disparate:]:
    shutil.copy(item, "disparate/"+item.split("/")[-1])