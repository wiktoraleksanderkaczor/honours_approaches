from progress.bar import Bar
import requests
import io
import os
import sys
import time

import concurrent.futures
from PIL import Image
import piexif
from fractions import Fraction
from tqdm import tqdm

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

    """
    for item in urls:
        thread_function(item, path)
    """
    tq = tqdm(total=len(urls))
    chunks_list = chunks(urls, WORKERS)
    for chunk in chunks_list:
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
            for url in chunk:
                executor.submit(thread_function, url, path, tq)

def to_deg(value, loc):
    """convert decimal coordinates into degrees, munutes and seconds tuple
    Keyword arguments: value is float gps-value, loc is direction list ["S", "N"] or ["W", "E"]
    return: tuple like (25, 13, 48.343 ,'N')
    """
    if value < 0:
        loc_value = loc[0]
    elif value > 0:
        loc_value = loc[1]
    else:
        loc_value = ""
    abs_value = abs(value)
    deg =  int(abs_value)
    t1 = (abs_value-deg)*60
    min = int(t1)
    sec = round((t1 - min)* 60, 5)
    return (deg, min, sec, loc_value)


def change_to_rational(number):
    """convert a number to rantional
    Keyword arguments: number
    return: tuple like (1, 2), (numerator, denominator)
    """
    f = Fraction(str(number))
    return (f.numerator, f.denominator)


def set_gps_location(file_name, lat, lng, altitude=None):
    """Adds GPS position as EXIF metadata
    Keyword arguments:
    file_name -- image file
    lat -- latitude (as float)
    lng -- longitude (as float)
    altitude -- altitude (as float)
    """
    lat_deg = to_deg(lat, ["S", "N"])
    lng_deg = to_deg(lng, ["W", "E"])

    exiv_lat = (change_to_rational(lat_deg[0]), change_to_rational(lat_deg[1]), change_to_rational(lat_deg[2]))
    exiv_lng = (change_to_rational(lng_deg[0]), change_to_rational(lng_deg[1]), change_to_rational(lng_deg[2]))

    gps_ifd = {
        piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
#        piexif.GPSIFD.GPSAltitudeRef: 1,
#        piexif.GPSIFD.GPSAltitude: change_to_rational(round(altitude)),
        piexif.GPSIFD.GPSLatitudeRef: lat_deg[3],
        piexif.GPSIFD.GPSLatitude: exiv_lat,
        piexif.GPSIFD.GPSLongitudeRef: lng_deg[3],
        piexif.GPSIFD.GPSLongitude: exiv_lng,
    }

    gps_exif = {"GPS": gps_ifd}

    # get original exif data first!
    exif_data = piexif.load(file_name)

    # update original exif data to include GPS tag
    exif_data.update(gps_exif)
    exif_bytes = piexif.dump(exif_data)

    piexif.insert(exif_bytes, file_name)

def thread_function(item, path, tq):
    image_name = item[0].split("/")[-1]
    image_path = os.path.join(path, image_name)

    if not os.path.isfile(image_path):  # ignore if already downloaded
        response=requests.get(item[0],stream=False)

        with open(image_path,'wb') as outfile:
            outfile.write(response.content)
    
        lat, lon = float(item[1]["lat"]), float(item[1]["lon"])
        set_gps_location(image_path, lat, lon)
    tq.update(1)

            
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
