import numpy as np
import json
import sys

def ecef2lla(x, y, z):
	# x, y and z are scalars or vectors in meters
	x = np.array([x]).reshape(np.array([x]).shape[-1], 1)
	y = np.array([y]).reshape(np.array([y]).shape[-1], 1)
	z = np.array([z]).reshape(np.array([z]).shape[-1], 1)

	a=6378137
	a_sq=a**2
	e = 8.181919084261345e-2
	e_sq = 6.69437999014e-3

	f = 1/298.257223563
	b = a*(1-f)

	# calculations:
	r = np.sqrt(x**2 + y**2)
	ep_sq  = (a**2-b**2)/b**2
	ee = (a**2-b**2)
	f = (54*b**2)*(z**2)
	g = r**2 + (1 - e_sq)*(z**2) - e_sq*ee*2
	c = (e_sq**2)*f*r**2/(g**3)
	s = (1 + c + np.sqrt(c**2 + 2*c))**(1/3.)
	p = f/(3.*(g**2)*(s + (1./s) + 1)**2)
	q = np.sqrt(1 + 2*p*e_sq**2)
	r_0 = -(p*e_sq*r)/(1+q) + np.sqrt(0.5*(a**2)*(1+(1./q)) - p*(z**2)*(1-e_sq)/(q*(1+q)) - 0.5*p*(r**2))
	u = np.sqrt((r - e_sq*r_0)**2 + z**2)
	v = np.sqrt((r - e_sq*r_0)**2 + (1 - e_sq)*z**2)
	z_0 = (b**2)*z/(a*v)
	h = u*(1 - b**2/(a*v))
	phi = np.arctan((z + ep_sq*z_0)/r)
	lambd = np.arctan2(y, x)

	return phi*180/np.pi, lambd*180/np.pi, h

path = sys.argv[-1]

with open(path) as f:
  data = json.load(f)

key_to_filename = {}
for view in data["views"]:
    key_to_filename[view["key"]] = view["value"]["ptr_wrapper"]["data"]["filename"]

key_to_gps = {}
for ext in data["extrinsics"]:
    key_to_gps[ext["key"]] = ext["value"]["center"]

recovered = {}
for key in key_to_gps.keys():
	x, y, z = key_to_gps[key][0], key_to_gps[key][1], key_to_gps[key][2]
	lat, lon, alt = ecef2lla(x, y, z)
	recovered[key_to_filename[key]] = {"lat": lat[0][0], "lon": lon[0][0]}
	print(key_to_filename[key], lat[0][0], lon[0][0])

with open(path.split("/")[-1].split(".")[-2] + "_positions.json", "w") as outfile:
	json.dump(recovered, outfile, indent=4)

