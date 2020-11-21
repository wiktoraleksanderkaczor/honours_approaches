import gzip
import pickle
import glob
import os
from shutil import copy as copyfile
from pprint import pprint

one_match = []
good_matches = []
zero_matches = []
total_matches = 0
for num, fname in enumerate(glob.glob("matches/*", recursive=True)):
	with gzip.open(fname, "rb") as f:
		data = pickle.load(f)
		num_matches = sum(1 for m in data.values() if len(m) > 0)
		total_matches += num_matches
		if num_matches == 1:
			#print(num, "-", fname, "=", num_matches)
			one_match.append({"filename": fname.split("/")[-1].split("_")[:-1][0], "num_matches": num_matches})
		elif num_matches > 1:
			good_matches.append({"filename": fname.split("/")[-1].split("_")[:-1][0], "num_matches": num_matches})
		else:
			zero_matches.append({"filename": fname.split("/")[-1].split("_")[:-1][0], "num_matches": num_matches})

pprint(zero_matches)
pprint(one_match)
pprint(good_matches)
print("TOTAL MATCHES:", total_matches)

images = "images/"
print(os.getcwd())
for item in good_matches:
	copyfile(images+item["filename"], "good_ones/"+item["filename"])

for item in one_match:
	copyfile(images+item["filename"], "bad_ones/"+item["filename"])

for item in zero_matches:
	copyfile(images+item["filename"], "no_match/"+item["filename"])
