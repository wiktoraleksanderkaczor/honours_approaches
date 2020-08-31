from progress.bar import Bar
import requests
import os
import sys
import time

import concurrent.futures

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

    for url in urls:
        image_name = url.split("/")[-1]
        image_path = os.path.join(path, image_name)

        if not os.path.isfile(image_path):  # ignore if already downloaded
            response=requests.get(url,stream=True)

            with open(image_path,'wb') as outfile:
                outfile.write(response.content)
