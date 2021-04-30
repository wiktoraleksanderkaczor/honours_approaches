from glob import glob
from scipy import stats
import numpy
import json

reconstructions = glob("reconstructions/*")

data = {}
for folder in reconstructions:
    with open(folder + "/openMVG/localised_accuracy.json", "r") as infile:
        temp = json.load(infile)
    
    images = [key for key in temp.keys() if key.endswith(".jpg")]
    metres_distances = [temp[image]["metres_distance_from_actual"] for image in images]
    
    sum_error = sum(metres_distances)
    average = numpy.average(metres_distances)
    median = numpy.median(metres_distances)
    mode = stats.mode(metres_distances)[0][0]
    max_val = numpy.max(metres_distances)
    min_val = numpy.min(metres_distances) 
    print(
        """
        FOLDER: {}
        SUM_ERROR: {}
        AVERAGE: {}
        MAX: {}
        MIN: {}
        IMAGES_LOCALISED: {}""".format(
            folder,
            round(sum_error, 3),
            round(average, 3),
            round(max_val, 3),
            round(min_val, 3),
            len(images)
            )
    )