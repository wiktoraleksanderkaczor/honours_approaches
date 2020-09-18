from bs4 import BeautifulSoup
import urllib.request
import re

headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}  
req = urllib.request.Request("https://www.google.com/search?tbm=isch&q=eiffel+tower", headers=headers)
#req = urllib.request.Request("https://imgur.com/search?q=eiffel%20tower", headers=headers)
html_page = urllib.request.urlopen(req)

soup = BeautifulSoup(html_page)
images = []
for img in soup.findAll('img'):
    a = img.get('src')
    b = img.get('data-src')
    alt = img.get('alt')
    if alt:
        print(alt)
    if a:
        images.append(a)
    if b:
        images.append(b)


#print(images)
