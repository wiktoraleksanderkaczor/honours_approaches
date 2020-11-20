import glob
from tqdm import tqdm

# These should already exist from the "Download"
compare_dir = "compare_set/"
data_dir = "images/"

compare_images = glob.glob(compare_dir+"*.jpg")
data_images = glob.glob(data_dir+"*.jpg")
data_pair_matching = "./data_pairs_to_match.txt"
compare_pair_matching = "./compare_pairs_to_match.txt"

print("Writing COMPARE images matching (exhaustive)")
for img1 in tqdm(compare_images):
    img1path = img1.split("/")[-1]
    for img2 in compare_images:
        img2path = img2.split("/")[-1]
        if img1 is not img2:
            to_write = img1path + " " + img2path + "\n"
            f = open(compare_pair_matching, "a").write(to_write)


# Write all image pairings for each data image to each comparison image but not to other data images.
print("Writing DATA images matching (all to compare)")

for data_img in tqdm(data_images):
    data_filename = data_img.split("/")[-1]

    for compare_img in compare_images:
        to_write = data_filename + " " + compare_img + "\n"
        f = open(data_pair_matching, "a").write(to_write)

