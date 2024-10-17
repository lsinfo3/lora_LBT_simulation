import json
import os
from glob import glob

import numpy as np
import scipy
from matplotlib import pyplot as plt


def plot_SF_histogram(filepath):
    with open(filepath, newline='') as jsonfile:
        data = json.load(jsonfile)
        res = [int(i) for i in data["SF"].values()]
        #print(res)
        plt.hist(res)
        plt.show()


source_folder = "results"
dirname = os.path.dirname(__file__)
inputpath = os.path.join(dirname, source_folder)
sensor_files = "placement_result*.json"
sensor_data_paths = [file
                     for path, subdir, files in os.walk(inputpath)
                     for file in glob(os.path.join(path, sensor_files))]

for i in sensor_data_paths:
    print(i)
    plot_SF_histogram(i)
