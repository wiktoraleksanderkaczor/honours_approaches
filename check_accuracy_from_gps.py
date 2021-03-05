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
    # Ground truth
    actual = None
    with open("gps_data_from_images.json", "r") as infile:
        actual = json.load(infile)

    # Within the reconstruction before localisation
    reconstructed_locations = None
    with open("sfm_data_geo_positions.json", "r") as infile:
        reconstructed_locations = json.load(infile)

    # Position after localisation
    localised = None
    with open("sfm_data_expanded_positions.json", "r") as infile:
        localised = json.load(infile)

    newly_localised_with_existing_gps = []
    used_for_georeferencing = []
    sum_error = 0
    for key in localised.keys():
        # Image was used for the actual georeferencing.
        if key in reconstructed_locations.keys() and key in actual.keys():
            used_for_georeferencing.append(key)

        # Image not used for georeferencing but as the only images used for localisation were those with GPS cleared... The image has accurate GPS.
        elif key in actual.keys() and key not in reconstructed_locations.keys():
            lat1, lat2 = localised[key]["lat"], actual[key]["lat"]
            lon1, lon2 = localised[key]["lon"], actual[key]["lon"]
            lat_distance = lat1 - lat2  
            lon_distance = lon1 - lon2
            newly_localised_with_existing_gps.append(key)
            metres_distance = measure(lat1, lon1, lat2, lon2)
            sum_error += metres_distance
            print(key + ":\n", \
                "actual_lat: {}, actual_lon: {}\n".format(lat2, lon2), \
                "localised_lat: {}, localised_lon: {}\n".format(lat1, lon1), \
                "lat_distance: {}, lon_distance: {}\n".format(lat_distance, lon_distance), \
                "distance in metres from desired position: {}m".format(metres_distance)) 
            print("\n")

    print("Localised, not contained within initial reconstruction, including used for georeferencing:", len(newly_localised_with_existing_gps))
    print("Initial, used for georeferencing:", len(used_for_georeferencing))
    print("Sum of acquired error:", sum_error)

if __name__ == "__main__":
    main()