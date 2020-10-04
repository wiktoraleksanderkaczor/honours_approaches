import os
import glob
from tqdm import tqdm

filenames = glob.glob("./tf_data/**/*.jpg", recursive = True)
#print(filenames)

def check_corrupt(filex):
    try:
        if (os.stat(filex).st_size == 0): #0 means bad file
            print(filex)
    except:
        print (filex)

# Are there any empty files?
for filex in tqdm(filenames):
    check_corrupt(filex)
