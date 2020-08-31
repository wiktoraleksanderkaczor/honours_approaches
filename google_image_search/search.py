import glob

import requests
import webbrowser

images_path = "./google_image_search/images/**/*.jpg"
only_files = glob.glob(images_path, recursive=True)
for filePath in only_files:
    searchUrl = 'http://www.google.hr/searchbyimage/upload'
    multipart = {'encoded_image': (filePath, open(filePath, 'rb')), 'image_content': ''}
    response = requests.post(searchUrl, files=multipart, allow_redirects=False)
    fetchUrl = response.headers['Location']
    webbrowser.open(fetchUrl)
    exec("")