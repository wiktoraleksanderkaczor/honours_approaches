from joblib import Parallel, delayed
from hashlib import md5
from tqdm import tqdm
import flickrapi
import requests
import json
import os


def links_from_flickr(topic):
    KEY = '88a8660edd2e770b1b00e878af174879'
    SECRET = 'f3063c276e3ad859'

    SIZES = ["url_o", "url_k", "url_h", "url_l",
             "url_c"]  # in order of preference

    """
    - url_o: Original (4520 × 3229)
    - url_k: Large 2048 (2048 × 1463)
    - url_h: Large 1600 (1600 × 1143)
    - url_l=: Large 1024 (1024 × 732)
    - url_c: Medium 800 (800 × 572)
    - url_z: Medium 640 (640 × 457)
    - url_m: Medium 500 (500 × 357)
    - url_n: Small 320 (320 × 229)
    - url_s: Small 240 (240 × 171)
    - url_t: Thumbnail (100 × 71)
    - url_q: Square 150 (150 × 150)
    - url_sq: Square 75 (75 × 75)
    """

    extras = ','.join(SIZES)
    flickr = flickrapi.FlickrAPI(KEY, SECRET, cache=True)
    week = 60*60*24*7
    flickr.cache = flickrapi.SimpleCache(timeout=week, max_entries=99999)

    photos = flickr.walk(text=topic,  # it will search by image title and image tags
                         extras=extras,  # get the urls for each size we want
                         privacy_filter=1,  # search only for public photos
                         per_page=50,
                         sort='relevance')  # we want what we are looking for to appear first

    counter = 0
    for photo in photos:
        got_photo = False
        for i in range(len(SIZES)):  # makes sure the loop is done in the order we want
            url = photo.get(SIZES[i])
            if url:  # if url is None try with the next size
                yield url
                got_photo = True
                break
        if not got_photo:
            counter += 1
        if counter >= 100:
            return


def download_task(link, tracker, folder):
    link_hash = str(md5(link.encode("utf-8")).hexdigest())
    ext = link.split(".")[-1].lower()
    fname = "image-{}.{}".format(link_hash, ext)

    path = os.path.join(folder, fname)

    if not os.path.isfile(path):
        try:
            myfile = requests.get(link, stream=True, timeout=5)
        except Exception as e:
            tracker["failed"][link] = str(e)
        else:
            open(path, 'wb').write(myfile.content)
            tracker["succeeded"][link] = fname
            tracker["len"] += 1


def download(links, folder):
    print("DOWNLOADING IMAGES FROM FLICKR:")
    if os.path.isfile("./logs/download_log_flickr.json"):
        with open("./logs/download_log_flickr.json", "r") as infile:
            tracker = json.load(infile)
    else:
        tracker = {"failed": {}, "succeeded": {}, "len": 0}

    Parallel(n_jobs=24, prefer="threads")(
        delayed(download_task)(link, tracker, folder) for link in tqdm(links)
    )

    with open("./logs/download_log_flickr.json", "w+") as outfile:
        json.dump(tracker, outfile, indent=4)
