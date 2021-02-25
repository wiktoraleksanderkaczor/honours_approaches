import json
from cmath import cos, sin, pi
from math import atan2, sqrt

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

def main():
    actual = None
    with open("gps_data_from_images.json", "r") as infile:
        actual = json.load(infile)

    reconstructed_locations = None
    with open("sfm_data_geo_positions.json", "r") as infile:
        reconstructed_locations = json.load(infile)

    localised = None
    with open("sfm_data_expanded_positions.json", "r") as infile:
        localised = json.load(infile)

    newly_localised_with_existing_gps = []
    used_for_georeferencing = []
    localised_by_reconstruction_no_existing_gps = []
    for key in localised.keys():
        # If image not in initial reconstruction.
        if key not in reconstructed_locations.keys() and key in actual.keys():
            lat1, lat2 = localised[key]["lat"], actual[key]["lat"]
            lon1, lon2 = localised[key]["lon"], actual[key]["lon"]
            lat_distance = lat1 - lat2  
            lon_distance = lon1 - lon2
            sum_distance = lon_distance + lat_distance
            newly_localised_with_existing_gps.append(key)
            metres_distance = measure(lat1, lon1, lat2, lon2)
            if metres_distance > 300:
                print("The image below is: {} {}".format(lat2, lon2))
            print(key, "-", "(sum_distance: {})".format(sum_distance), "(lat: {}, lon: {})".format(lat_distance, lon_distance), "distance in metres: {}".format(metres_distance))
        if key in reconstructed_locations.keys() and key in actual.keys():
            used_for_georeferencing.append(key)
        if key in reconstructed_locations.keys() and key not in actual.keys():
            localised_by_reconstruction_no_existing_gps.append(key)

    print("Number of images localised using georeferenced reconstruction, not contained within the reconstruction and with previous known GPS:", len(newly_localised_with_existing_gps))
    print("Number of images included in reconstruction with known prior GPS, presumably used for georeferencing:", len(used_for_georeferencing))
    print("Number of newly localised, unknown prior GPS:", len(localised_by_reconstruction_no_existing_gps))


if __name__ == "__main__":
    main()