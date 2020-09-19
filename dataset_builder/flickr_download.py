from progress.bar import Bar
import requests
import os
import sys
import time
import flickrapi
import concurrent.futures

WORKERS = 8

"""
    Before downloading the photos we need to make sure the folder where we are going to save them actually exist, otherwise you might get an error.
"""
def create_folder(path):
    if not os.path.isdir(path):
        os.makedirs(path)

"""
And finally we can download them.
"""
def download_images(urls, path):
    create_folder(path)  # makes sure path exists

    from tqdm import tqdm
    tq = tqdm(total=len(urls))

    chunks_list = chunks(urls, WORKERS)
    for chunk in chunks_list:
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
            for url in chunk:
                executor.submit(thread_function, url, path, tq)

def thread_function(url, path, tq):
    image_name = url.split("/")[-1]
    image_path = os.path.join(path, image_name)

    if not os.path.isfile(image_path):  # ignore if already downloaded
        response=requests.get(url,stream=True)

        with open(image_path,'wb') as outfile:
            outfile.write(response.content)
        
        tq.update(1)

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
        
KEY = '88a8660edd2e770b1b00e878af174879'
SECRET = 'f3063c276e3ad859'

#SIZES = ["url_o", "url_k", "url_h", "url_l", "url_c"]  # in order of preference
SIZES = ["url_l"]  # in order of preference


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

"""
    Now we can do the search using “flickr.walk” which returns an iterable object.
"""
def get_photos(image_tag):
    extras = ','.join(SIZES)
    flickr = flickrapi.FlickrAPI(KEY, SECRET)
    photos = flickr.walk(text=image_tag,  # it will search by image title and image tags
                            extras=extras,  # get the urls for each size we want
                            privacy_filter=1,  # search only for public photos
                            per_page=50,
                            sort='relevance')  # we want what we are looking for to appear first
    return photos

"""
    And this function will allow us to get the URL for a photo following our list of sizes.
"""
def get_url(photo):
    for i in range(len(SIZES)):  # makes sure the loop is done in the order we want
        url = photo.get(SIZES[i])
        if url:  # if url is None try with the next size
            return url


"""
    Putting those two functions together we can get all the images we want with the desired size.
"""
def get_urls(image_tag, max):
    photos = get_photos(image_tag)
    counter=0
    interval = max // 10
    urls=[]

    for photo in photos:
        if counter < max:
            url = get_url(photo)  # get preffered size url
            if url:
                urls.append(url)
                counter += 1
                if counter % interval == 0:
                    print(counter, "/", max)
            # if no url for the desired sizes then try with the next photo
        else:
            break

    return urls

"""
    MASSIVE WORK IN PROGESS
"""
def get_tags(related):
    flickr = flickrapi.FlickrAPI(KEY, SECRET, format="parsed-json")
    tags = flickr.tags.getClusters(tag=related)
    return tags
    
"""
    Putting everything together in main.py we have.
"""

def download(topic, num_images):
    print("Getting urls for", topic)
    urls = get_urls(topic, num_images)
    
    print("Downloading images for", topic)
    path = "./dataset_builder/images"

    download_images(urls, path)

