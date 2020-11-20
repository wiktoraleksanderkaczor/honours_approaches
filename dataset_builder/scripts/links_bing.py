from common import *

def links_from_bing(topic, max_images, exts=["jpg", "png", "jpeg"], adult="off", bing_filter="filterui:imagesize-custom_640_480"):
    links = []
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0'}
    image_counter = 0
    page_counter = 0

    tq = tqdm(total = max_images)
    while image_counter < max_images:
        # Parse the page source and download pics
        request_url = 'https://www.bing.com/images/async?q=' + urllib.parse.quote_plus(topic) \
                        + '&first=' + str(page_counter) + '&count=' + str(max_images) \
                        + '&adlt=' + adult + '&qft=' + bing_filter
        request = urllib.request.Request(request_url, None, headers=headers)
        response = urllib.request.urlopen(request)
        html = response.read().decode('utf8')
        found_links = re.findall('murl&quot;:&quot;(.*?)&quot;', html)

        for link in found_links:
            if image_counter < max_images:
                try:
                    path = urllib.parse.urlsplit(link).path
                    filename = posixpath.basename(path).split('?')[0]
                    file_type = filename.split(".")[-1]
                    link = link[:link.index("."+file_type)]+"."+file_type
                    if file_type.lower() in exts:
                        links.append(link)
                        image_counter += 1
                        tq.update(1)
                except:
                    pass
            else:
                break

        page_counter += 1
    tq.close()
    return links
