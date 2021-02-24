from common import *

def generate_image_list(data_dir):
	files = glob.glob("{}*.jpg".format(data_dir), recursive=True)

	with open("output/image_list.txt", "w+") as outfile:
		for line in files:
			line = line.split("/")[-1]
			outfile.write(line + "\n")
