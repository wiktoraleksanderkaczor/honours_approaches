import pickle
import glob
import imagehash
from PIL import Image

with open("hashed.pickle", "rb") as handle:
    hashed_load = pickle.load(handle)

files = glob.glob("./to_check", recursive = True)

for i in files:
    hash_check = imagehash.dhash(Image.open(i))
    