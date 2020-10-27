import glob
from tqdm import tqdm
from pprint import pprint
from cmath import cos, sin, pi
from math import atan2, sqrt, ceil, floor
from statistics import mode, median_low, median_grouped, median_high, median, mean
from shutil import move

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

files = glob.glob("images/*.jpg", recursive=True)

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
        print(val)
print("NUM_TUPLES: ", num_tuples)

# To cartesian coords, as colmap is expecting
cartesian = {}
all_gps = []
for key, val in tag_paths.items():
    if type(val) is not tuple or type(val) is not Exception:
        if "Latitude" in val.keys() and "Longitude" in val.keys():
            x, y, z = get_cartesian(val["Latitude"], val["Longitude"])
            new_key = key.split("/")[-1]
            cartesian[new_key] = {"X": x, "Y": y, "Z": z}
            all_gps.append((new_key, val["Latitude"], val["Longitude"]))

pprint(cartesian)
print("LENGTH CARTESIAN: ", len(cartesian))


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

gps_seg = {"fname": [], "lat": [], "lon": []}
lat_only = []
lon_only = []
for item in all_gps:
    (fname, lat, lon) = item
    lat_only.append(int(lat))
    lon_only.append(int(lon))
    gps_seg["fname"].append(fname)
    gps_seg["lat"].append(lat)
    gps_seg["lon"].append(lon)

lat_freq = mode(lat_only)
lon_freq = mode(lon_only)
print("LAT:", lat_freq, "LON:", lon_freq)

bad = []
for fname, lat, lon in zip(gps_seg["fname"], gps_seg["lat"], gps_seg["lon"]):
    if abs(lat - lat_freq) > 1 and abs(lon - lon_freq) > 1:
        bad.append(fname)

bad = list(set(bad))
for item in bad:
    try:
        move("images/"+item, "bad_gps/")
    except Exception as e:
        print(item, e)
#pprint(all_dis)
