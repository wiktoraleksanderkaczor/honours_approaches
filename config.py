from geopy.geocoders import Nominatim


# The topic for the reconstruction.
TOPIC = "Edinburgh Castle Scotland"

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

# The GPS location for the subject of choice.
geolocator = Nominatim(user_agent="honours_dissertation-wiktor_kaczor")
location = geolocator.geocode(TOPIC)
