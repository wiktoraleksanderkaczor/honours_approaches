import os
import sys 
import cv2
import time
import glob
import shutil
import pickle
import sqlite3
import fnmatch
import copyreg
import subprocess
from math import exp
from PIL import Image
import multiprocessing
from pprint import pprint
import concurrent.futures
from tqdm import tqdm

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def thread_it(thread_function, my_list, tq=True, WORKERS=None):
    # Set worker number to CPU count
    if not WORKERS:
        WORKERS = multiprocessing.cpu_count()
    
    if tq:
        tq = tqdm(total=len(my_list))
    
    # Separate into chunks and execute threaded
    thread_list = chunks(my_list, WORKERS)
    for chunk in thread_list:
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
            for item in chunk:
                executor.submit(thread_function, item)
                if tq:
                    tq.update(1)
    tq.close()



def thread_it_return(thread_function, my_list, tq=True, WORKERS=None):
    # Set worker number to CPU count
    if not WORKERS:
        WORKERS = multiprocessing.cpu_count()
    
    if tq:
        tq = tqdm(total=len(my_list))
        
    results = []
    # Separate into chunks and execute threaded
    thread_list = chunks(my_list, WORKERS)
    for chunk in thread_list:
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
            for item in chunk:
                future = executor.submit(thread_function, item)
                
                return_value = future.result()
                if return_value != None:
                    results.append(return_value)
                    
                if tq:
                    tq.update(1)
    
    tq.close()
    
    return results
    

def create_folder(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def move_to(file_list, dest):
    tq = tqdm(total=len(file_list))
    exception_flag = False
    for item in file_list:
        try:
            shutil.move(item, dest)
        except Exception as e:
            print(e)
            exception_flag = True
        tq.update(1)
    tq.close()
    return exception_flag

# These should already exist from the "Download"
compare_dir = "compare_set/"
data_dir = "images/"

compare_images = glob.glob(compare_dir+"*.jpg")
data_images = glob.glob(data_dir+"*.jpg")
data_pair_matching = "./data_pairs_to_match.txt"
compare_pair_matching = "./compare_pairs_to_match.txt"

print("Writing COMPARE images matching (exhaustive)")
tq = tqdm(total=len(compare_images))
for img1 in compare_images:
    img1path = img1.split("/")[-1]
    for img2 in compare_images:
        img2path = img2.split("/")[-1]
        if img1 is not img2:
            to_write = img1path + " " + img2path + "\n"
            f = open(compare_pair_matching, "a").write(to_write)
    tq.update(1)
tq.close()

# Write all image pairings for each data image to each comparison image but not to other data images.
print("Writing DATA images matching (all to compare)")
tq = tqdm(total=len(data_images))
for data_img in data_images:
    data_filename = data_img.split("/")[-1]

    for compare_img in compare_images:
        to_write = data_filename + " " + compare_img + "\n"
        f = open(data_pair_matching, "a").write(to_write)
    tq.update(1)
tq.close()
