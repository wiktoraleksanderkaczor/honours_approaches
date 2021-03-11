from geopy.geocoders import Nominatim


TOPIC = "Edinburgh Castle Scotland"
METRES_RADIUS_THRESHOLD = 750
BLURRINESS_THRESHOLD = 125
PIXEL_NUM_THRESHOLD = 307200
CLOSE_IMAGE_THRESHOLD = 5
NUM_LARGEST_IMAGES = 500
NUM_GPS_IMAGES = 10

geolocator = Nominatim(user_agent="honours_dissertation-wiktor_kaczor")
location = geolocator.geocode(TOPIC)
