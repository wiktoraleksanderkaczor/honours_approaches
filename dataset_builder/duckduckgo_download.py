import requests 
import re 
import json 
import time 
import logging 

import concurrent.futures
from tqdm import tqdm
from random import randint

logging.basicConfig(level=logging.ERROR) 
logger = logging.getLogger(__name__)

def printJson(objs, count=0):
    links = []
    for obj in objs:
        """
        print("Width {0}, Height {1}".format(obj["width"], obj["height"]))
        print("Thumbnail {0}".format(obj["thumbnail"]))
        print("Url {0}".format(obj["url"]))
        print("Title {0}".format(obj["title"].encode('utf-8')))
        print("Image {0}".format(obj["image"]))
        
        -- EXAMPLE OUTPUT --
        Width 3840, Height 2560
        Thumbnail https://tse1.mm.bing.net/th?id=OIF.BrhofaJg5Fx2yl9jrBBQLQ&pid=Api
        Url https://www.airantares.ro/cazare/in-Paris/Franta/beaugrenelle-eiffel-tour-3-stars-paris-franta/
        Title b'Beaugrenelle Tour Eiffel, Paris, Franta'
        Image https://i.travelapi.com/hotels/2000000/1070000/1063000/1062936/c5a49732.jpg
        """

        if (obj["width"] * obj["height"]) > 307200:
            links.append(obj["image"])
        # EXAMPLE OUTPUT

    return links

def search(keywords):
    pages = []

    url = 'https://duckduckgo.com/' 
    params = {
    	'q': keywords
    } 

    logger.debug("Hitting DuckDuckGo for Token") 

    #   First make a request to above URL, and parse out the 'vqd'
    #   This is a special token, which should be used in the subsequent request
    res = requests.post(url, data=params)
    searchObj = re.search(r'vqd=([\d-]+)\&', res.text, re.M|re.I) 

    if not searchObj:
        logger.error("Token Parsing Failed !") 
        return -1 

    logger.debug("Obtained Token") 

    headers = {
        'authority': 'duckduckgo.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'sec-fetch-dest': 'empty',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'referer': 'https://duckduckgo.com/',
        'accept-language': 'en-US,en;q=0.9',
    }

    params = (
        ('l', 'us-en'),
        ('o', 'json'),
        ('q', keywords),
        ('vqd', searchObj.group(1)),
        ('f', ',,,'),
        ('p', '1'),
        ('v7exp', 'a'),
    )

    requestUrl = url + "i.js"

    logger.debug("Hitting Url : %s", requestUrl)

    while True:
        while True:
            try:
                res = requests.get(requestUrl, headers=headers, params=params)
                data = json.loads(res.text)
                break
            except ValueError as e:
                logger.debug("Hitting Url Failure - Sleep and Retry: %s", requestUrl)
                time.sleep(5)
                continue

        logger.debug("Hitting Url Success : %s", requestUrl)
        pages.append(printJson(data["results"]))

        if "next" not in data:
            logger.debug("No Next Page - Exiting")
            return pages

        requestUrl = url + data["next"] 


def thread_function(lst_item, folder, extensions, tq):
    num, item = lst_item
    myfile = requests.get(item, allow_redirects=True)

    # Any exceptions shouldn't exit the program since this is a thread.
    fname = item.split("/")[-1].split(".")[-2]
    ext = item.split(".")[-1][:3]
    if ext.lower() in extensions:
        path = folder+str(fname)+str(num)+'.'+ext
        open(path, 'wb').write(myfile.content)
        tq.update(1)

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def download_from_ddg(topic, folder):
    pages = search(topic) 
    print("Pages: ", len(pages))
    total = 0
    for links in pages:
        total += len(links)
    print("Total: ", total)

    extensions = ["jpg", "png", "bmp", "jpeg"]
    flat_list = [item for sublist in pages for item in sublist]
    tq = tqdm(total=len(flat_list))
    WORKERS = 8
    chunks_list = chunks(list(enumerate(flat_list)), WORKERS)
    for chunk in chunks_list:
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
            for item in chunk:
                executor.submit(thread_function, item, folder, extensions, tq)