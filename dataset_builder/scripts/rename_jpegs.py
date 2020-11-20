from common import *

def img_rename(image):
    fname = image.split(".")[-2]
    ext = image.split(".")[-1]
    if ext == "jpeg":
        shutil.move(image, fname+".jpg")
    elif ext == "jpg":
        return
    else:
        return
                
def images_rename(path):
    files = glob.glob(path+"*.*", recursive=True)
    thread_it(img_rename, files)

