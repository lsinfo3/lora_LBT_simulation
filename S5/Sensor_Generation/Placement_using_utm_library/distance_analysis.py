import csv

import pandas as pd
import numpy as np
import math
import utm

def calculateDistance(x1, x2, y1, y2):
    return math.sqrt(math.pow(x1 - x2, 2) + math.pow(y1 - y2, 2))

if __name__ == "__main__":
    Distances=[]
    Sensors = []
    Sensors2= []
    output = {"x": [], "y": []}
    with open("sensors_UTM.csv", newline='') as csvfile:
        data = list(csv.reader(csvfile))
        for curr in data:
            try:
                Sensors.append([float(curr[0]), float(curr[1])])
            except:
                pass
    with open("sensors.csv", newline='') as csvfile:
        data = list(csv.reader(csvfile))
        for curr in data:
            try:
                Sensors2.append([float(curr[0]), float(curr[1])])
            except:
                pass
    for sens in range(len(Sensors)):
        Distances.append(calculateDistance(Sensors[sens][0],Sensors2[sens][0],Sensors[sens][1],Sensors2[sens][1]))
    print (np.mean(Distances))
    print(np.std(Distances))