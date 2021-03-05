import numpy as np
import cv2
from tqdm import tqdm

MAX_MATCHES = 10
"""
index_params = dict(algorithm=6,
                    table_number=6,
                    key_size=12,
                    multi_probe_level=2)
search_params = {}
flann = cv2.FlannBasedMatcher(index_params, search_params)
"""

bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)


def get_num_matches(cur_frame, last_frame):

    kp1, des1 = cur_frame
    kp2, des2 = last_frame

    matches = bf.knnMatch(des1, des2, k=2)

    # As per Lowe's ratio test to filter good matches
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)

    #print(len(good_matches))
    if len(good_matches) > MAX_MATCHES:
        return True
    else:
        return False

#Get video name from user
#Ginen video name must be in quotes, e.g. "pirkagia.avi" or "plaque.avi"
video_name = input("Please give the video name including its extension. E.g. \"pirkagia.avi\":\n")

#Cut the video extension to have the name of the video
my_video_name = video_name.split(".")[0]

#Open the video file
cap = cv2.VideoCapture(video_name)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# Init
orb = cv2.ORB_create(nfeatures=1024)
desc = []
for i in tqdm(range(total_frames)):
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    kp1, des1 = orb.detectAndCompute(gray, None)
    if i == 0:
        last_frame = des1
    desc.append(des1)

for i in tqdm(range(desc)):
    j = i+1
    good_match = get_num_matches(desc[i], desc[j])
    if good_match:
        last_frame = desc[j]

    if good_match:
        #Store this frame to an image
        cv2.imwrite(my_video_name+'_frame_'+str(j)+'.jpg',gray)

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()