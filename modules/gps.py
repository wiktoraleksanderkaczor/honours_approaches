from fileio import create_folder, filename, copy
from joblib import Parallel, delayed
from cmath import cos, sin, pi
from GPSPhoto import gpsphoto
from math import atan2, sqrt
from shutil import move
from PIL import Image
from tqdm import tqdm
from glob import glob
import numpy as np
import simplekml
import exifread
import json
import os


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
    gps_bearing = _get_if_exist(exif_data, 'GPS GPSDestBearing')
    gps_direction = _get_if_exist(exif_data, 'GPS GPSImgDirection')

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
        if gps_altitude_ref.values[0] == 1:
            altitude *= -1

    bearing = None
    if gps_bearing or gps_direction:
        bearing = True

    return lat, lon, altitude, bearing


# Distance between two points
def measure(lat1, lon1, lat2, lon2):  # generally used geo measurement function
    R = 6378.137  # Radius of earth in KM
    dLat = lat2 * pi / 180 - lat1 * pi / 180
    dLon = lon2 * pi / 180 - lon1 * pi / 180
    a = sin(dLat/2) * sin(dLat/2) + \
        cos(lat1 * pi / 180) * \
        cos(lat2 * pi / 180) * \
        sin(dLon/2) * sin(dLon/2)
    a = a.real
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    d = R * c
    return d * 1000  # meters


def get_gps(data_dir, some_gps, good_gps, bad_gps, location, METRES_THR=500):
    files = glob("{}*.jpg".format(data_dir), recursive=True)

    images_with_gps = {}
    nothing = []
    for image in tqdm(files):
        try:
            lat, lon, alt, bearing = get_exif_location(get_exif_data(image))
            if lat and lon:
                # Not really good but there seem to be a lot of images that just say 0m, have to filter.
                if alt and alt != 0:
                    images_with_gps[image] = {
                        "lat": lat, "lon": lon, "alt": alt, "bearing": bearing}
            else:
                nothing.append(image)
        except Exception as e:
            nothing.append((image, e))

    print("GPS FOUND FOR:", len(images_with_gps.keys()))
    print("NOT FOUND FOR:", len(nothing))

    incorrect_items, correct_items = {}, {}
    for image in images_with_gps.keys():
        distance = measure(images_with_gps[image]["lat"], images_with_gps[image]["lon"],
                           location.latitude, location.longitude)
        if distance < METRES_THR:
            correct_items[image] = distance
        else:
            incorrect_items[image] = distance

    for item in incorrect_items.keys():
        move(item, bad_gps + filename(item))

    to_save = {}
    for item in correct_items.keys():
        fname = filename(item)
        # If image has bearing tag.
        if images_with_gps[item]["bearing"]:
            move(item, good_gps + fname)
            to_save[fname] = images_with_gps[item]
        else:
            move(item, some_gps + fname)

    with open("intermediate/gps_data_from_images.json", "w") as outfile:
        json.dump(to_save, outfile, indent=4)


def remove_exif(some_gps, cleared_gps):
    images = glob(some_gps+"/*")
    # https://stackoverflow.com/questions/19786301/python-remove-exif-info-from-images
    for image in tqdm(images):
        try:
            photo = gpsphoto.GPSPhoto(image)
            photo.stripData(cleared_gps + filename(image))
        except:
            print(image + "- FALLBACK TO FULL CLEAR")
            img = Image.open(image)
            data = list(img.getdata())
            img_without_exif = Image.new(img.mode, img.size)
            img_without_exif.putdata(data)
            img_without_exif.save(cleared_gps+filename(image))


def select_and_copy_GPS_images(data_dir, good_gps, NUM_GPS_IMAGES, NUM_LARGEST_IMAGES, openMVG_images):
    # Load previous images used if the file exists.
    gps_images = []
    if os.path.isfile("logs/images_for_georeferencing.json"):
        with open("logs/images_for_georeferencing.json", "r") as infile:
            gps_images = json.load(infile)
    
    # Sort possible GPS images by size (maximise ability to be included) and set number to be 
    # added to minus what is already there.
    possible_gps = sorted(glob(good_gps+"*.jpg"), key=os.path.getsize, reverse=True)

    # Add only enough images to fill the quota, not removing those there. 
    # If there aren't enough, all will be used.
    for image in possible_gps:
        if len(gps_images) >= NUM_GPS_IMAGES:
            break
        if image not in gps_images:
            gps_images.append(image)

    # Save the images for later.
    with open("logs/images_for_georeferencing.json", "w+") as outfile:
        json.dump(gps_images, outfile, indent=4)

    # Move images to folder
    for image in gps_images:
        copy(image, openMVG_images + filename(image))

    # Sort by size and move the amount needed.
    sorted_by_size = sorted(glob(data_dir+"*.jpg"), key=os.path.getsize, reverse=True)

    images_used = []
    if os.path.isfile("logs/images_used.json"):
        with open("logs/images_used.json", "r") as infile:
            images_used = json.load(infile)

    for image in sorted_by_size:
        if len(images_used) >= NUM_LARGEST_IMAGES:
            break
        if image not in images_used:
            images_used.append(image)
            copy(image, openMVG_images + filename(image))

    with open("logs/images_used.json", "w+") as outfile:
        json.dump(images_used, outfile, indent=4)


def convert_to_kml(georeference, output="openMVG/positions.kml"):
    with open(georeference, "r") as infile:
        data = json.load(infile)

    kml = simplekml.Kml()

    for key, values in data.items():
        #https://simplekml.readthedocs.io/en/latest/geometries.html
        #https://simplekml.readthedocs.io/en/latest/constants.html#simplekml.AltitudeMode
        kml.newpoint(name=key, coords=[(values["lon"], values["lat"], values["alt"])], altitudemode="absolute")

    kml.save(output)


def ecef2lla(x, y, z):
    # x, y and z are scalars or vectors in meters
    x = np.array([x]).reshape(np.array([x]).shape[-1], 1)
    y = np.array([y]).reshape(np.array([y]).shape[-1], 1)
    z = np.array([z]).reshape(np.array([z]).shape[-1], 1)

    a = 6378137
    a_sq = a**2
    e = 8.181919084261345e-2
    e_sq = 6.69437999014e-3

    f = 1/298.257223563
    b = a*(1-f)

    # calculations:
    r = np.sqrt(x**2 + y**2)
    ep_sq = (a**2-b**2)/b**2
    ee = (a**2-b**2)
    f = (54*b**2)*(z**2)
    g = r**2 + (1 - e_sq)*(z**2) - e_sq*ee*2
    c = (e_sq**2)*f*r**2/(g**3)
    s = (1 + c + np.sqrt(c**2 + 2*c))**(1/3.)
    p = f/(3.*(g**2)*(s + (1./s) + 1)**2)
    q = np.sqrt(1 + 2*p*e_sq**2)
    r_0 = -(p*e_sq*r)/(1+q) + np.sqrt(0.5*(a**2)*(1+(1./q)) -
                                      p*(z**2)*(1-e_sq)/(q*(1+q)) - 0.5*p*(r**2))
    u = np.sqrt((r - e_sq*r_0)**2 + z**2)
    v = np.sqrt((r - e_sq*r_0)**2 + (1 - e_sq)*z**2)
    z_0 = (b**2)*z/(a*v)
    h = u*(1 - b**2/(a*v))
    phi = np.arctan((z + ep_sq*z_0)/r)
    lambd = np.arctan2(y, x)

    return phi*180/np.pi, lambd*180/np.pi, h


def export_gps_to_file(georeference, output="openMVG/"):
    with open(georeference) as f:
        data = json.load(f)

    key_to_filename = {}
    for view in data["views"]:
        key_to_filename[view["key"]
                        ] = view["value"]["ptr_wrapper"]["data"]["filename"]

    key_to_gps = {}
    for ext in data["extrinsics"]:
        key_to_gps[ext["key"]] = ext["value"]["center"]

    recovered = {}
    for key in key_to_gps.keys():
        x, y, z = key_to_gps[key][0], key_to_gps[key][1], key_to_gps[key][2]
        lat, lon, alt = ecef2lla(x, y, z)
        recovered[key_to_filename[key]] = {"lat": lat[0][0], "lon": lon[0][0], "alt": alt[0][0]}
        #print(key_to_filename[key], lat[0][0], lon[0][0])

    no_ext = filename(georeference).split(".")[-2]
    with open(output + no_ext + "_positions.json", "w") as outfile:
        json.dump(recovered, outfile, indent=4)

import write_gps

def gps_to_img_task(img, val, workspace_folder, new_gps_images_folder):
    try:
        lat, lon, alt = val["lat"], val["lon"], val["alt"]
        img_path = glob(workspace_folder + "/**/" + img)[0]
        photo = write_gps.GPSPhoto(img_path)
        info = write_gps.GPSInfo((lat, lon), alt=int(alt))
        # Try to write with new GPS, fallback to just copying it over.
        try:
            photo.modGPSData(info, new_gps_images_folder + img)
        except:
            copy(img_path, new_gps_images_folder + img)
    except Exception as e:
        print(img, e)


def export_gps_to_images(positions, workspace_folder="openMVG/", new_gps_images_folder="openMVG/localization_images_new_gps/"):
    with open(positions) as f:
        data = json.load(f)

    create_folder(new_gps_images_folder)
    print("WRITING GPS TO IMAGES")
    Parallel(n_jobs=24, prefer="threads")(
        delayed(gps_to_img_task)(img, val, workspace_folder, new_gps_images_folder) \
            for img, val in tqdm(data.items()) \
            if not os.path.isfile(new_gps_images_folder + img)
    )


def get_accuracy(gps_data, sfm_geo_positions, sfm_expanded_positions, output=None):
    # Ground truth
    with open(gps_data, "r") as infile:
        actual = json.load(infile)

    # Position after localisation
    with open(sfm_expanded_positions, "r") as infile:
        localised = json.load(infile)

    # Getting difference to check which images were newly localised.
    with open(sfm_geo_positions, "r") as infile:
        geo_positions = json.load(infile)
    localised_images = [img for img in localised.keys() if img not in geo_positions.keys()]

    with open("logs/not_used_for_georeferencing.json", "r") as infile:
        not_used_for_georeferencing = json.load(infile) 
    not_used_for_georeferencing = [filename(img) for img in not_used_for_georeferencing]

    newly_localised = {}
    sum_error = 0
    for key in localised.keys():
        # Image not used for georeferencing but as the only images used for localisation were those with GPS cleared... The image has accurate GPS.
        if key in actual.keys() and key in localised_images and key in not_used_for_georeferencing:
            lat1, lat2 = localised[key]["lat"], actual[key]["lat"]
            lon1, lon2 = localised[key]["lon"], actual[key]["lon"]
            alt1, alt2 = localised[key]["alt"], actual[key]["alt"]
            lat_distance = lat1 - lat2
            lon_distance = lon1 - lon2
            alt_distance = alt1 - alt2
            metres_distance = measure(lat1, lon1, lat2, lon2)
            sum_error += metres_distance
            newly_localised[key] = {
                "actual": {"lat": lat2, "lon": lon2, "alt": alt2},
                "localised": {"lat": lat1, "lon": lon1, "alt": alt1},
                "change_in_coords": {"lat_change": lat_distance, "lon_change": lon_distance, "alt_change": alt_distance},
                "metres_distance_from_actual": metres_distance
            }

    newly_localised["sum_error"] = sum_error

    if output:
        json.dump(newly_localised, open(output, "w+"), indent=4)
