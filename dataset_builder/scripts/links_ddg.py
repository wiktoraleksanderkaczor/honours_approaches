def extract_json(objs, exts):
    links = []
    for obj in objs:
        """
        print("Width {0}, Height {1}".format(obj["width"], obj["height"]))
        print("Thumbnail {0}".format(obj["thumbnail"]))
        print("Url {0}".format(obj["url"]))
        print("Title {0}".format(obj["title"].encode('utf-8')))
        print("Image {0}".format(obj["image"]))

        -- EXAMPLE OUTPUT --
        Width 3840, Height 2560
        Thumbnail https://tse1.mm.bing.net/th?id=OIF.BrhofaJg5Fx2yl9jrBBQLQ&pid=Api
        Url https://www.airantares.ro/cazare/in-Paris/Franta/beaugrenelle-eiffel-tour-3-stars-paris-franta/
        Title b'Beaugrenelle Tour Eiffel, Paris, Franta'
        Image https://i.travelapi.com/hotels/2000000/1070000/1063000/1062936/c5a49732.jpg
        """

        if (obj["width"] * obj["height"]) > 307200 and obj["image"].split(".")[-1].lower() in exts:
            links.append(obj["image"])

    return links


def links_from_ddg(topic, max_images=None, exts=["jpg", "png", "jpeg"]):
    link_list = []

    url = 'https://duckduckgo.com/'
    params = {'q': topic}

    #   First make a request to above URL, and parse out the 'vqd'
    #   This is a special token, which should be used in the subsequent request
    res = requests.post(url, data=params)
    searchObj = re.search(r'vqd=([\d-]+)\&', res.text, re.M|re.I)

    if not searchObj:
        # Token parsing failed
        return -1

    headers = {
        'authority': 'duckduckgo.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'sec-fetch-dest': 'empty',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'referer': 'https://duckduckgo.com/',
        'accept-language': 'en-US,en;q=0.9',
    }

    params = (
        ('l', 'us-en'),
        ('o', 'json'),
        ('q', topic),
        ('vqd', searchObj.group(1)),
        ('f', ',,,'),
        ('p', '1'),
        ('v7exp', 'a'),
    )

    requestUrl = url + "i.js"

    print("Scraping links from DuckDuckGo")
    tq = tqdm(total=max_images)
    link_count = 0
    while True:
        while True:
            try:
                res = requests.get(requestUrl, headers=headers, params=params)
                data = json.loads(res.text)
                break
            except ValueError:
                # Hitting Url Failure - Sleep and Retry
                time.sleep(5)
                continue

        links = extract_json(data["results"], exts)
        for link in links:
            if max_images and link_count != max_images:
                link_list += [link]
                link_count += 1
                tq.update(1)
            else:
                return link_list


        if "next" not in data:
            # No next page
            return link_list

        requestUrl = url + data["next"]
