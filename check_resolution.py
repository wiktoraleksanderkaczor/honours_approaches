from common import *

def res_check_thread(image):
    img = cv2.imread(image, cv2.IMREAD_GRAYSCALE)

    # Get image height and width
    #height, width, channels = img.shape
    height, width = img.shape

    # Count maximum resolution
    val = width * height
    
    # Show warning if problem
    # 640*480
    if val < 307200:
        return image


def get_under_res(path):
    files = glob.glob(path+"*.jpg")
    under_res = thread_it_return(res_check_thread, files)
    
    return under_res
