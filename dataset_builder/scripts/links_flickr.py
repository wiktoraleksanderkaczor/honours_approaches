def links_from_flickr(topic, max_images):
    KEY = '88a8660edd2e770b1b00e878af174879'
    SECRET = 'f3063c276e3ad859'

    SIZES = ["url_o", "url_k", "url_h", "url_l", "url_c"]  # in order of preference

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
    
    extras = ','.join(SIZES)
    flickr = flickrapi.FlickrAPI(KEY, SECRET)
    photos = flickr.walk(text=topic,  # it will search by image title and image tags
                            extras=extras,  # get the urls for each size we want
                            privacy_filter=1,  # search only for public photos
                            per_page=50,
                            sort='relevance')  # we want what we are looking for to appear first
    counter, urls = 0, []

    print("Scraping links from Flickr")
    tq = tqdm(total = max_images)
    for photo in photos:
        if counter < max_images:
            for i in range(len(SIZES)):  # makes sure the loop is done in the order we want
                url = photo.get(SIZES[i])
                if url:  # if url is None try with the next size
                    urls.append(url)
                    counter += 1
                    tq.update(1)
                    break
        else:
            break

    return urls
