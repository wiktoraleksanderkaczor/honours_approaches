import flickrapi

KEY = '88a8660edd2e770b1b00e878af174879'
SECRET = 'f3063c276e3ad859'

SIZES = ["url_o", "url_k", "url_h", "url_l", "url_c"]  # in order of preference
#SIZES = ["url_l"]  # in order of preference
flickrloc = flickrapi.FlickrAPI(KEY, SECRET, format="parsed-json")

from tqdm import tqdm
"""
- url_o: Original (4520 × 3229)
- url_k: Large 2048 (2048 × 1463)
- url_h: Large 1600 (1600 × 1143)
- url_l=: Large 1024 (1024 × 732)
- url_c: Medium 800 (800 × 572)
- url_z: Medium 640 (640 × 457)
- url_m: Medium 500 (500 × 357)
- url_n: Small 320 (320 × 229)
- url_s: Small 240 (240 × 171)
- url_t: Thumbnail (100 × 71)
- url_q: Square 150 (150 × 150)
- url_sq: Square 75 (75 × 75)
"""

"""
    Now we can do the search using “flickr.walk” which returns an iterable object.
"""
def get_photos(image_tag):
    extras = ','.join(SIZES)
    flickr = flickrapi.FlickrAPI(KEY, SECRET)
    photos = flickr.walk(text=image_tag,  # it will search by image title and image tags
                            extras=extras,  # get the urls for each size we want
                            privacy_filter=1,  # search only for public photos
                            per_page=50,
                            sort='relevance')  # we want what we are looking for to appear first
    return photos

"""
    And this function will allow us to get the URL for a photo following our list of sizes.
"""
def get_url(photo):
    for i in range(len(SIZES)):  # makes sure the loop is done in the order we want
        url = photo.get(SIZES[i])
        if url:  # if url is None try with the next size
            return url

def get_location(photo_id):
    try:
        location = flickrloc.photos.geo.getLocation(photo_id=photo_id)
        lat = location["photo"]["location"]["latitude"]
        lon = location["photo"]["location"]["longitude"]
        return {"lat": lat, "lon": lon}
    except Exception:
        pass
"""
    Putting those two functions together we can get all the images we want with the desired size.
"""
def get_urls(image_tag, max):
    photos = get_photos(image_tag)
    counter=0
    urls=[]
    t = tqdm(total=max)
    for photo in photos:
        if counter < max:
            url = get_url(photo) # get preffered size url
            location = get_location(photo.attrib["id"])
            if url and location:
                urls.append((url, location))
                counter += 1
                t.update(1)
            # if no url for the desired sizes then try with the next photo
        else:
            break

    return urls


