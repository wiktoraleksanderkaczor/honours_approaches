from geopy.geocoders import Nominatim


# The topic for the reconstruction.
TOPIC = "St Giles Cathedral Outside"
GEO_TOPIC = "St Giles Cathedral"

# Number of metres around the GPS location of the subject to be considered valid GPS.
METRES_RADIUS_THRESHOLD = 750

# Anything under this Laplacian varience number to be considered NOT blurry.
BLURRINESS_THRESHOLD = 125

# Amount of pixels in an image to be considered a big enough images.
PIXEL_NUM_THRESHOLD = 307200

# The threshold for image hashing for an image to be considered a duplicate.
CLOSE_IMAGE_THRESHOLD = 5

# Number of images (separate from GPS ones) to be passed to openMVG.
NUM_LARGEST_IMAGES = 500
# Number of GPS images (separate from above) to be passed to openMVG.
NUM_GPS_IMAGES = 15

# NORMAL or HIGH
DESCRIBER_PRESET = "NORMAL"

# Refinement reconstruction using localised images.
IMAGES_CLUSTER_NUM = 60
ONLY_N_BIGGEST = 500
# Video links, can be empty.
VIDEO_LINKS = []
FRAMES_PER_SECOND = 1

# NORMAL or HIGH
REFINEMENT_DESCRIBER_PRESET = "HIGH"

# The GPS location for the subject of choice.
geolocator = Nominatim(user_agent="honours_dissertation-wiktor_kaczor")
location = geolocator.geocode(GEO_TOPIC)
