import cv2
import os



def grayscale(path, dstpath):
    # Create folder if it doesn't already exist.
    try:
        os.makedirs(dstpath)
    except:
        print ("Directory already exist, images will be written in same folder")

    # List all files in source path.
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))] 

    max_resolution = 0

    # Process each image, ensure minimum size, and grayscale before writing in dst path.
    for image in files:
        try:
            img = cv2.imread(os.path.join(path,image))
            
            #height, width, channels = img.shape
            height, width, _ = img.shape

            # Ensure minimum size.
            # 640x480
            val = width * height
            if val < 307200:
                print("{} is too small in resolution".format(image))
                continue
            if val > max_resolution:
                max_resolution = val

            # Make grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            dstPath = os.path.join(dstpath,image)
            cv2.imwrite(dstPath,gray)
        except:
            print ("{} is not converted".format(image))
            
    return max_resolution
        