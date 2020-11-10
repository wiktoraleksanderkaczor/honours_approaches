import re
import os
import cv2
import wget
import json
import glob
import pickle
import shutil
import urllib
import hashlib
import requests
import flickrapi
import imagehash
import posixpath
from PIL import Image
from skimage import io
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
