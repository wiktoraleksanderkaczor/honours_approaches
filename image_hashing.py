from common import *

def hash_thread(item):
    fname = item["image"]
    hashes = item["hashes"]
    if fname not in hashes.keys():
        hashes[fname] = imagehash.dhash(Image.open(fname))


def compute_img_hashes(path):
    items = []
    files = glob.glob(path+"*.jpg", recursive=True)
    pickle_output = "intermediate/pickles/image_hashes.pickle"
    if os.path.isfile(pickle_output):
        hashes = pickle.load(open(pickle_output, "rb"))
    else:
        hashes = {}
    for image in files:
        items.append({"image": image, "hashes": hashes})
    
    thread_it(hash_thread, items)
    pickle.dump(hashes, open(pickle_output, "wb"))


def hash_distance_thread(item):
    image = item["image"]
    hashes = item["hashes"]
    distances = item["distances"]
    hash1 = hashes[image]

    for hash2name in hashes.keys():
        # If not same image, and not already done for that image
        if hash2name != image and hash2name not in distances[image].keys():
            hash2 = hashes[hash2name]
            distances[image][hash2name] = hash1 - hash2


def compute_hash_distance(path, pickle_output="intermediate/pickles", pickle_input="intermediate/pickles"):
    hashes_path = "intermediate/pickles/image_hashes.pickle"
    distances_path = "intermediate/pickles/image_distances.pickle"
    files = glob.glob(path+"*.jpg", recursive=True)
    if os.path.isfile(hashes_path):
        hashes = pickle.load(open(hashes_path, "rb"))
    else:
        print("No hash file detected, cannot continue.")
        return

    if os.path.isfile(distances_path):
        distances = pickle.load(open(distances_path, "rb"))
    else:
        distances = {}
    
    for image in files:
        distances[image] = {}

    items = []
    for image in files:
        items.append({"image": image, "hashes": hashes, "distances": distances})

    thread_it(hash_distance_thread, items)
    pickle.dump(distances, open(distances_path, "wb"))


def get_duplicate_images(path, threshold=10):
    distances_path = "intermediate/pickles/image_distances.pickle"
    if os.path.isfile(distances_path):
        distances = pickle.load(open(distances_path, "rb"))
    else:
        print("No distances file detected, cannot continue.")
        return

    files = glob.glob(path+"*.jpg", recursive=True)
    dup, close = [], []
    
    for path in files:
        distances_item = distances[path]
        img = path.split(".")[-2]+".jpg"
        
        for key, val in distances_item.items():
            if val == 0:
                if key not in dup and path not in dup:
                    dup.append(key)
            elif val < threshold:
                if key not in close and path not in close:
                    close.append(key)
                
    return dup, close