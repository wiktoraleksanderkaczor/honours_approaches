import glob

files = glob.glob("compare_set/*.jpg", recursive=True)

f = open("image_match.txt", "w")
for line in files:
    line = line.split("/")[-1]
    f.write(line + "\n")
f.close()