from common import *

def generate_image_list(data_dir):
	files = glob.glob("{}*.jpg".format(data_dir), recursive=True)

	f = open("output/image_list.txt", "w")
	for line in files:
	    line = line.split("/")[-1]
	    f.write(line + "\n")
	f.close()
