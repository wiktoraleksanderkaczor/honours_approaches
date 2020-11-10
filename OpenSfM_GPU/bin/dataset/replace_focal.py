import glob
import json

lines = open("scaled_focal.txt", "r").readlines()
new_focal = {}
for line in lines:
    focal = line.split(" ")[1]
    fname = line.split(" ")[0]
    new_focal[fname] = float(focal)

files = glob.glob("exif/*", recursive=True)
camera_models = json.load(open("camera_models.json"))

for path in files:
    fname = path.split("/")[-1][:-5]
    data = json.load(open(path))
    camera = data["camera"]
    if "unknown" in camera:
        camera_models[camera]["focal"] = new_focal[fname]
        data["focal_ratio"] = new_focal[fname]
        json.dump(data, open(path, "w"), indent=4)

    


with open("camera_models.json", "w") as json_file:
  json.dump(camera_models, json_file, indent=4)