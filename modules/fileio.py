import os
import shutil


dirs = [
    "intermediate/",
    "intermediate/images",
    "intermediate/too_blurry",
    "intermediate/cleared_gps",
    "intermediate/cleared_some_gps",
    "intermediate/duplicates",
    "intermediate/good_gps",
    "intermediate/bad_gps",
    "intermediate/some_gps",
    "intermediate/too_small",
    "openMVG/images",
    "openMVG/localization_images",
    "openMVG/some_gps_localization",
    "openMVG/some_gps_localization_output",
    "reconstructions/",
    "logs/",
    "video",
    "video/downloads/",
    "video/extracted/",
]


def create_folder(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def filename(path):
    return path.split("/")[-1]


def move(path, dest):
    try:
        #os.symlink(path, dest)
        shutil.move(path, dest)
    except Exception as e:
        print(e)


def copy(path, dest):
    try:
        shutil.copyfile(path, dest)
    except Exception as e:
        print(e)


if __name__ == "fileio":
    for path in dirs:
        create_folder(path)
