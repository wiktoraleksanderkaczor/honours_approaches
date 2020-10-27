import glob
from tqdm import tqdm
from pprint import pprint
from cmath import cos, sin

from GPSPhoto import gpsphoto
# Converting lat/long to cartesian
import numpy as np

def get_cartesian(lat=None,lon=None):
    lat, lon = np.deg2rad(lat), np.deg2rad(lon)
    R = 6371 # radius of the earth
    x = R * np.cos(lat) * np.cos(lon)
    y = R * np.cos(lat) * np.sin(lon)
    z = R *np.sin(lat)
    return x,y,z

files = glob.glob("**/*.jpg", recursive=True)

tag_paths = {}
tq = tqdm(total=len(files))
for image in files:
    """
    exif = get_exif(image)
    geotags = get_geotagging(exif)
    if geotags != None:
        try:
            tag_paths[image] = geotags
        except Exception as e:
            print(image, ";", e)
    """
    try:
        data = gpsphoto.getGPSData(image)
    except Exception as e:
        data = {}
        #data = (image, e)
    if len(data) != 0:
        tag_paths[image] = data
    tq.update(1)

pprint(tag_paths)
print("LENGTH: ", len(tag_paths))

num_tuples = 0
for key, val in tag_paths.items():
    if type(val) is tuple:
        num_tuples += 1
print("NUM_TUPLES: ", num_tuples)

# To cartesian coords, as colmap is expecting
cartesian = {}
for key, val in tag_paths.items():
    if type(val) is not tuple or type(val) is not Exception:
        if "Latitude" in val.keys() and "Longitude" in val.keys():
            x, y, z = get_cartesian(val["Latitude"], val["Longitude"])
            new_key = key.split("/")[-1]
            cartesian[new_key] = {"X": x, "Y": y, "Z": z}

pprint(cartesian)
print("LENGTH CARTESIAN: ", len(cartesian))