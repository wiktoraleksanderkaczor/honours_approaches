from common import *
from GPSPhoto import gpsphoto
from cmath import cos, sin, pi
from math import atan2, sqrt, ceil, floor
from statistics import mode, median_low, median_grouped, median_high, median, mean
from shutil import move

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

# Converting lat/long to cartesian
def get_cartesian(lat=None,lon=None):
    lat, lon = np.deg2rad(lat), np.deg2rad(lon)
    R = 6371 # radius of the earth
    x = R * np.cos(lat) * np.cos(lon)
    y = R * np.cos(lat) * np.sin(lon)
    z = R *np.sin(lat)
    return x,y,z

def get_gps(data_dir):
    files = glob.glob("{}*.jpg".format(data_dir), recursive=True)

    tag_paths = {}
    for image in tqdm(files):
        try:
            data = gpsphoto.getGPSData(image)
        except:
            data = None
        if data:
            tag_paths[image] = data

    print("Tag paths:")
    pprint(tag_paths)
    print("Length of tag paths: ", len(tag_paths))

    num_tuples = 0
    for _, val in tag_paths.items():
        if type(val) is tuple:
            num_tuples += 1
    print("Number of tuples: ", num_tuples)

    # To Cartesian coordinates, as COLMAP is expecting
    cartesian = {}
    gps_seg = {"fname": [], "lat": [], "lon": []}
    lat_only = []
    lon_only = []
    for key, val in tag_paths.items():
        if type(val) is not tuple or type(val) is not Exception:
            if "Latitude" in val.keys() and "Longitude" in val.keys():
                x, y, z = get_cartesian(val["Latitude"], val["Longitude"])
                cartesian[key] = {"X": x, "Y": y, "Z": z}
                gps_seg["fname"].append(key)
                gps_seg["lat"].append(val["Latitude"])
                gps_seg["lon"].append(val["Longitude"])
                lat_only.append(int(val["Latitude"]))
                lon_only.append(int(val["Longitude"]))

    pprint(cartesian)
    print("LENGTH CARTESIAN: ", len(cartesian))

    lat_freq = mode(lat_only)
    lon_freq = mode(lon_only)
    print("LAT_FREQ:", lat_freq, "LON_FREQ:", lon_freq)
    for fname, lat, lon in zip(gps_seg["fname"], gps_seg["lat"], gps_seg["lon"]):
        if abs(lat - lat_freq) > 1 and abs(lon - lon_freq) > 1:
            try:
                move(fname, "bad_gps/")
            except:
                pass
