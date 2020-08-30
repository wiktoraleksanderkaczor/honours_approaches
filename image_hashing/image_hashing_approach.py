import glob
from PIL import Image
import glob
import imagehash
from tqdm import tqdm
import random
from pprint import pprint
import concurrent.futures
import multiprocessing
import pickle


WORKERS = 8

# Function to split list into chunks.
def chunks(lst, n):
    # Yield successive n-sized chunks from lst.
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def thread_hash(chunk, key, hashed):
	for i in chunk:
		hash1 = imagehash.dhash(Image.open(i))
		hashed.append(hash1)

if __name__ == "__main__":
    # ONLY DOING TRAIN LIKE NORMAL
    #files = glob.glob("./**/*.jpg", recursive=True)
    files = glob.glob("./train/**/*.jpg", recursive=True)
    files_sorted, hashed, hash_list = {}, {}, []
    for i in files:
        folder = i.split("/")[-2]
        filename = i.split("/")[-1]
        if folder not in files_sorted.keys():
            files_sorted[folder] = [i]
        else:
            files_sorted[folder].append(i)

    for key in tqdm(files_sorted.keys()):
        hash_list = []
        hashed[key] = []
        chunks_list = chunks(files_sorted[key], WORKERS)        
        for chunk in chunks_list:
            with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
                executor.submit(thread_hash, chunk, key, hash_list)
        del(chunks_list)
        hashed[key] = hash_list

    with open("hashed.pickle", "wb") as handle:
        pickle.dump(hashed, handle, protocol=pickle.HIGHEST_PROTOCOL)

    pprint(hashed)

    """
    with open("hashed.pickle", "rb") as handle:
        hashed_load = pickle.load(handle)
    """
