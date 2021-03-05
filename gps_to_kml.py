import json
import simplekml

with open("sfm_data_geo_positions.json", "r") as infile:
    data = json.load(infile)

kml = simplekml.Kml()

for key, values in data.items():
    kml.newpoint(name=key, coords=[(values["lon"], values["lat"])])

kml.save("positions.kml")