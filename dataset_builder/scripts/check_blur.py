from common import *

def too_blurry_thread(item):
    image = item["image"]
    threshold = item["threshold"]
    img = cv2.imread(image, cv2.IMREAD_GRAYSCALE)
    val = cv2.Laplacian(img, cv2.CV_64F).var()
    if val < threshold:
        return image
                
def get_too_blurry(path, threshold):
    files = glob.glob(path+"*.jpg")
    items = []
    for image in files:
        items.append({"image": image, "threshold": threshold})
    too_blurry = thread_it_return(too_blurry_thread, items)
    
    print("{} out of {} images are blurry".format(len(too_blurry), len(files)))
    return too_blurry
