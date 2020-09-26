import cv2
import os
from tqdm import tqdm
import sys 
import shutil
from pprint import pprint
from chunks import chunks
import concurrent.futures

def get_blur_thr(path, files):
    thr = 0
    for image in files:
        img = cv2.imread(os.path.join(path,image))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thr += cv2.Laplacian(gray, cv2.CV_64F).var()
    return thr / len(files)

def process_thread(path, image, too_small, too_blurry, small, blurry, default_blur_thr, dstpath, avg_res, max_resolution, tq):
    # Update counter
    tq.update(1)
    
    # Get image path and load it
    img_path = os.path.join(path, image)
    img = cv2.imread(img_path)

    # Get image height and width
    #height, width, channels = img.shape
    height, width, _ = img.shape

    # Count maximum resolution
    val = width * height
    max_resolution.append(val)

    # Ensure minimum size.
    # 640x480
    if val < 307200:
        too_small.append(img_path)
        shutil.move(img_path, small)
    else:
        # Make grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Blur detection
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        if variance < default_blur_thr:
            too_blurry.append(img_path)
            shutil.move(img_path, blurry)
        else:
            avg_res.append(val)

            # If image already exists at destination, continue.
            dstPath = os.path.join(dstpath,image)

            if not os.path.isfile(dstPath):
                # Write image to destination
                cv2.imwrite(dstPath, gray)


def grayscale(path, dstpath, small, blurry, ref_blur=None, do_print=False):
    print("Converting images to grayscale: ")
    avg_res = []

    # Create folder if it doesn't already exist.
    try:
        os.makedirs(dstpath)
    except:
        print ("Directory already exist, images will be written in same folder")

    # List all files in source path.
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))] 

    max_resolution, default_blur_thr = [], None
    if not ref_blur:
        ref_blur = get_blur_thr(path, files)
        default_blur_thr = 0
    else:
        # Technically speaking, ref blur at this point, is peak sharpness.
        # I think that 75% of peak sharpness is still sharp enough, will test
        #default_blur_thr = ref_blur
        default_blur_thr = ref_blur * 0.85

    tq = tqdm(total=len(files))

    too_blurry = []
    too_small = []

    # Process each image, ensure minimum size, and grayscale before writing in dst path.
    # MULTI_THREADED:
    WORKERS = 4
    chunks_list = chunks(files, WORKERS)
    for chunk in chunks_list:
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
            for image in chunk:
                executor.submit(process_thread, path, image, too_small, too_blurry, small, blurry, default_blur_thr, dstpath, avg_res, max_resolution, tq)

    if do_print:
        print("Images too small: ")
        pprint(too_small)
        print("Images too blurry: ")
        pprint(too_blurry)
    
    return max(max_resolution), ref_blur, sum(avg_res)/len(avg_res)
        
if __name__ == "__main__":
    import download
    download.runner()