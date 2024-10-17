import json
import os
from glob import glob

import numpy as np
import math
import scipy
from matplotlib import pyplot as plt

def payload_size_to_time(payload, sf):
    # data_rate_optimisation: BW 125kHz, SF>=11
    BW = 125
    PL = payload + 3
    CR = 4
    CRC = 1
    H = 1
    DE = 0
    SF = sf
    npreamble = 8
    if (sf >= 11):
        DE = 0

    Rs = BW / (math.pow(2, SF))
    Ts = 1 / (Rs)
    symbol = 8 + max(math.ceil((8.0 * PL - 4.0 * SF + 28 + 16 * CRC - 20.0 * H) /
                               (4.0 * (SF - 2.0 * DE))) * (CR + 4), 0)
    Tpreamble = (npreamble + 4.25) * Ts
    Tpayload = symbol * Ts
    ToA = Tpreamble + Tpayload
    return ToA

def plot_SF_histogram(filepath):
    with open(filepath, newline='') as jsonfile:
        data = json.load(jsonfile)
        res = [int(i) for i in data["SF"].values()]
        toplot=[]
        for pl in range(1,52):
            for curr in res:
                toplot.append(payload_size_to_time(pl,curr))
        toas=[]
        for sf in range(7,13):
            for pl in range(1,52):
                toas.append(payload_size_to_time(pl,sf))
        toas=(sorted(list(set(toas))))
        toa_distrib=list(list(np.histogram(toplot,bins=toas))[0])
        print(scipy.stats.describe(toplot))
        print(scipy.stats.bayes_mvs(toplot))
        plt.hist(toplot,bins=toas)
        plt.show()


source_folder = "collisioncalc"
dirname = os.path.dirname(__file__)
inputpath = os.path.join(dirname, source_folder)
sensor_files = "*.json"
sensor_data_paths = [file
                     for path, subdir, files in os.walk(inputpath)
                     for file in glob(os.path.join(path, sensor_files))]

for i in sensor_data_paths:
    print(i)
    plot_SF_histogram(i)
