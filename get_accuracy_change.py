import glob
import json

reconstructions = glob.glob("../*")
reconstructions = [folder for folder in reconstructions if "~" not in folder]
original_locations = {}

for folder in reconstructions:
    with open(folder+"/openMVG/localised_accuracy.json", "r") as infile:
        data = json.load(infile)

    for key, val in data.items():
        if key != "sum_error":
            original_locations[key] = val["localised"]
            original_locations[key]["metres_distance_from_actual"] = val["metres_distance_from_actual"]

from cmath import cos, sin, pi
from math import atan2, sqrt

# https://stackoverflow.com/a/38187562
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

with open("openMVG/localised_accuracy.json", "r") as infile:
    data = json.load(infile)
    new_locations = {key: val["localised"] for key, val in data.items() if key != "sum_error"}
    changes = {"missing": []}
    all_images = []
    metres_distance_from_actual_changes = []
    metres_distance_changes = []
    for key, val in new_locations.items():
        if key not in all_images:
            all_images.append(key)
        if key in original_locations:
            old = original_locations[key]
            if key not in changes:
                changes[key] = {}
            metres_distance_change = measure(old["lat"], old["lon"], val["lat"], val["lon"])
            changes[key]["change"] = metres_distance_change
            metres_distance_changes.append(metres_distance_change) 
            metres_distance_from_actual_change = data[key]["metres_distance_from_actual"] - old["metres_distance_from_actual"]
            changes[key]["metres_distance_from_actual_change"] = metres_distance_from_actual_change
            metres_distance_from_actual_changes.append(metres_distance_from_actual_change)
        else:
            changes["missing"].append(key)

    from pprint import pprint
    pprint(changes)
    print("ALL_IMAGES:", len(all_images))
    print("IMAGES MISSING:", len(changes["missing"]))
    print("METRES DISTANCE FROM ACTUAL CHANGE SUM:", round(sum(metres_distance_from_actual_changes), 3))
    print("METRES DISTANCE CHANGE SUM:", round(sum(metres_distance_changes), 3))
