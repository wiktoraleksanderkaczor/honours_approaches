from check_similarity import *
import glob
from pprint import pprint


dir_names = glob.glob("../../tf_train/train/*")
pprint(dir_names)

stats_for_dirs = []
for i in dir_names:
    print(i)
    stats_for_dirs.append(check_stats(i))

pprint(stats_for_dirs)
