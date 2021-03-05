import re
import os
import cv2
import wget
import json
import glob
import pickle
import shutil
import urllib
import random
import hashlib
import requests
import flickrapi
import imagehash
import posixpath
import numpy as np
from PIL import Image
from tqdm import tqdm
from skimage import io
import multiprocessing
from pprint import pprint
import concurrent.futures
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="honours_dissertation-wiktor_kaczor")

def split_list(to_split):
    half = len(to_split)//2
    return to_split[:half], to_split[half:]


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
    

def thread_download(item):
    link = item["link"]
    folder = item["folder"]
    service = item["service"]
    tracker = item["tracker"]
    link_hash = str(hashlib.md5(link.encode("utf-8")).hexdigest())
    ext = link.split(".")[-1].lower()
    fname = "image-{}.{}".format(link_hash, ext)
    
    path = os.path.join(folder, fname)

    if not os.path.isfile(path):
        try:
            myfile = None
            if service == "ddg":
                myfile = requests.get(link, allow_redirects=True, timeout=0.5)
            elif service == "flickr":
                myfile = requests.get(link, stream=True, timeout=0.5)
            elif service == "bing":
                myfile = requests.get(link, timeout=0.5)
            open(path, 'wb').write(myfile.content)
            tracker["succeeded"][fname] = link
            #wget.download(link, path)
        except Exception as e:
            tracker["failed"].append(link)
        

def download(links, folder, service="flickr"):
    items = []
    tracker = {"failed": [], "succeeded": {}}
    for link in links:
        items.append({"link": link, "folder": folder, "service": service, "tracker": tracker})
    print("Downloading links from {} to {}".format(service, folder))
    thread_it(thread_download, items, WORKERS=None)
    with open("./logs/download_log_{}.json".format(service), "w+") as outfile:
        json.dump(tracker, outfile, indent=4)
