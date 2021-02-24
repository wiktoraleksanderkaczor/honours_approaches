from common import *
#from GPSPhoto import gpsphoto
import exifread
from cmath import cos, sin, pi
from math import atan2, sqrt, ceil, floor
from statistics import mode, median_low, median_grouped, median_high, median, mean
from shutil import move
import json

from PIL import Image
from GPSPhoto import gpsphoto

def _get_if_exist(data, key):
    if key in data:
        return data[key]

    return None

def _convert_to_degress(value):
    """
    Helper function to convert the GPS coordinates stored in the EXIF to degress in float format
    :param value:
    :type value: exifread.utils.Ratio
    :rtype: float
    """
    d = float(value.values[0].num) / float(value.values[0].den)
    m = float(value.values[1].num) / float(value.values[1].den)
    s = float(value.values[2].num) / float(value.values[2].den)

    return d + (m / 60.0) + (s / 3600.0)

def get_exif_data(image_file):
    with open(image_file, 'rb') as f:
        exif_tags = exifread.process_file(f)
    return exif_tags 

def get_exif_location(exif_data):
    """
    Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data above)
    """
    lat = None
    lon = None

    gps_latitude = _get_if_exist(exif_data, 'GPS GPSLatitude')
    gps_latitude_ref = _get_if_exist(exif_data, 'GPS GPSLatitudeRef')
    gps_longitude = _get_if_exist(exif_data, 'GPS GPSLongitude')
    gps_longitude_ref = _get_if_exist(exif_data, 'GPS GPSLongitudeRef')
    gps_altitude_ref = _get_if_exist(exif_data, 'GPS GPSAltitudeRef')
    gps_altitude = _get_if_exist(exif_data, 'GPS GPSAltitude')

    if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
        lat = _convert_to_degress(gps_latitude)
        if gps_latitude_ref.values[0] != 'N':
            lat = 0 - lat

        lon = _convert_to_degress(gps_longitude)
        if gps_longitude_ref.values[0] != 'E':
            lon = 0 - lon 

    altitude = None
    if gps_altitude and gps_altitude_ref:
        alt = gps_altitude.values[0]
        altitude = alt.num / alt.den
        if gps_altitude_ref.values[0] == 1: altitude *= -1

    return lat, lon, altitude

# Distance between two points
def measure(lat1, lon1, lat2, lon2): # generally used geo measurement function
    R = 6378.137 # Radius of earth in KM
    dLat = lat2 * pi / 180 - lat1 * pi / 180
    dLon = lon2 * pi / 180 - lon1 * pi / 180
    a = sin(dLat/2) * sin(dLat/2) + \
        cos(lat1 * pi / 180) * \
        cos(lat2 * pi / 180) * \
        sin(dLon/2) * sin(dLon/2)
    a = a.real
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    d = R * c
    return d * 1000 # meters

from collections import Counter 
  
def most_frequent(List): 
    occurence_count = Counter(List) 
    return occurence_count.most_common(1)[0][0] 

# Converting lat/long to cartesian
def get_cartesian(lat=None,lon=None):
    lat, lon = np.deg2rad(lat), np.deg2rad(lon)
    R = 6371 # radius of the earth
    x = R * np.cos(lat) * np.cos(lon)
    y = R * np.cos(lat) * np.sin(lon)
    z = R *np.sin(lat)
    return x,y,z

def get_gps(data_dir, good_gps, bad_gps):
    files = glob.glob("{}*.jpg".format(data_dir), recursive=True)

    tag_paths = {}
    nothing = []
    for image in files:
        try:
            lat, lon, alt = get_exif_location(get_exif_data(image))
            if lat and lon:
                tag_paths[image] = {"lat": lat, "lon": lon, "alt": alt}
            else:
                nothing.append(image)
        except Exception as e:
            #print(image, "-", e)
            nothing.append((image, e))

    print("Tag paths:", len(tag_paths))
    print("Nothing found for:", len(nothing))

    sum_distances = {}
    for key1, val1 in tag_paths.items():
        total = 0
        for key2, val2 in tag_paths.items():
            if key1 != key2:
                total += measure(val1["lat"], val1["lon"], val2["lat"], val2["lon"])
        sum_distances[key1] = total
    
    pprint(sum_distances)
    from sklearn.cluster import KMeans
    import numpy as np
    training_data = np.array(list(sum_distances.values())).reshape(-1, 1)
    kmeans = KMeans(n_clusters=2).fit_predict(training_data)
    
    correct = most_frequent(kmeans)
    incorrect_items, correct_items = [], []
    for image, cluster in zip(sum_distances.keys(), kmeans):
        if cluster != correct:
            print(image, "-", cluster)
            incorrect_items.append(image)
        else:
            correct_items.append(image)
    
    for item in incorrect_items:
        move(item, bad_gps + item.split("/")[-1])

    to_save = {}
    for item in correct_items:
        move(item, good_gps + item.split("/")[-1])
        removed_path = item.split("/")[-1]
        to_save[removed_path] = tag_paths[item]

    with open("intermediate/gps_data_from_images.json", "w") as outfile:
        json.dump(to_save, outfile, indent=4)

def remove_exif(good_gps, cleared_gps):
    images = glob.glob(good_gps+"/*")
    # https://stackoverflow.com/questions/19786301/python-remove-exif-info-from-images
    for image in tqdm(images):
        try:
            photo = gpsphoto.GPSPhoto(image)
            photo.stripData(cleared_gps + image.split("/")[-1])
        except Exception as e:
            print(image, e, "- FALLBACK TO FULL CLEAR")
            img = Image.open(image)

            # next 3 lines strip exif
            data = list(img.getdata())
            img_without_exif = Image.new(img.mode, img.size)
            img_without_exif.putdata(data)

            img_without_exif.save(cleared_gps+image.split("/")[-1])

if __name__ == "__main__":
    from run import *