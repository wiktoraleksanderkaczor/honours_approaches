import os
import cv2

dist_folder = 'folder_to_save_undistorted_images'
if not os.path.exists(dist_folder):
    os.makedirs(dist_folder)

fileID = open('path_to_txt_file','r').readlines()
xi = 1.08