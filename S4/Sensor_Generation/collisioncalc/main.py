import csv
import math

import numpy as np
import pandas as pd
import utm as utm


def calculateDistance(x1, x2, y1, y2):
    return math.sqrt(math.pow(x1 - x2, 2) + math.pow(y1 - y2, 2))


def hata(gw_height, sf):
    sens_height = 1
    # represents Spreading Factor Tolerances for Path Loss in dB
    plrange = [131, 134, 137, 140, 141, 144]
    distance = 10 ** (-(69.55 + 76.872985 - 13.82 * math.log10(gw_height) - 3.2 * (math.log10(
        11.75 * sens_height) ** 2) + 4.97 - plrange[sf - 7]) / (44.9 - 6.55 * math.log10(gw_height)))
    return distance * 1000


if __name__ == '__main__':
    Sensors = {"id": [], "x": [], "y": [], "BestGW": [], "SF": [], "NumberOfSensors": [], "NumGWs": [],
               "IsGateway": []}
    with open("results/placement_results.csv", newline='') as csvfile:
        data = list(csv.reader(csvfile))
        for curr in data:
            try:
                Sensors["id"].append(int(curr[0]))
                Sensors["x"].append(float(curr[1]))
                Sensors["y"].append(float(curr[2]))
                Sensors["BestGW"].append(int(curr[3]))
                Sensors["SF"].append(int(curr[4]))
                Sensors["NumberOfSensors"].append(int(curr[5]))
                Sensors["NumGWs"].append(int(curr[6]))
                Sensors["IsGateway"].append(curr[7] == "True")
            except:
                pass
    tempsensors = utm.from_latlon(np.array(Sensors["y"]), np.array(Sensors["x"]))
    zonenumber = [tempsensors[2], tempsensors[3]]
    tempsensors = [tempsensors[0].tolist(), tempsensors[1].tolist()]
    for i in range(len(tempsensors[0])):
        Sensors["x"][i] = tempsensors[0][i]
        Sensors["y"][i] = tempsensors[1][i]
    print(zonenumber)
    output = {"lon": [], "lat": [], "BestGW": Sensors["BestGW"], "SF": Sensors["SF"],
              "NumberOfSensors": Sensors["NumberOfSensors"], "NumGWs": Sensors["NumGWs"], "distance": [],
              "range": [0 for i in range(len(Sensors["id"]))],
              "sf_collisions": [[0, 0, 0, 0, 0, 0] for i in range(len(Sensors["id"]))],
              "gw_x": [], "gw_y": [], "sen_x": [], "sen_y": []}
    for x in range(len(Sensors["id"])):
        coords = utm.to_latlon(Sensors["x"][x], Sensors["y"][x], zonenumber[0], zonenumber[1], strict=False)
        output["lat"].append(coords[0])
        output["lon"].append(coords[1])
        output["distance"].append(hata(15, int(Sensors["SF"][x])))
        output["range"][x] += Sensors["NumberOfSensors"][x]
        output["sf_collisions"][x][int(Sensors["SF"][x]) - 7] += Sensors["NumberOfSensors"][x]
        output["gw_x"].append(Sensors["x"][int(Sensors["BestGW"][x])])
        output["gw_y"].append(Sensors["y"][int(Sensors["BestGW"][x])])
        output["sen_x"].append(Sensors["x"][x])
        output["sen_y"].append(Sensors["y"][x])
    for x in range(len(Sensors["id"])):
        for y in range(x + 1, len(Sensors["id"])):
            if x != y:
                g = Sensors["BestGW"][x]

                if calculateDistance(Sensors["x"][x], Sensors["x"][y], Sensors["y"][x], Sensors["y"][y]) < \
                        output["distance"][y]:
                    output["range"][x] += Sensors["NumberOfSensors"][y]
                    output["sf_collisions"][x][int(Sensors["SF"][x]) - 7] += Sensors["NumberOfSensors"][y]

                elif calculateDistance(Sensors["x"][g], Sensors["x"][y], Sensors["y"][g], Sensors["y"][y]) < \
                        output["distance"][y]:
                    output["range"][x] += Sensors["NumberOfSensors"][y]
                    output["sf_collisions"][x][int(Sensors["SF"][x]) - 7] += Sensors["NumberOfSensors"][y]
    pd.DataFrame(data=output).to_csv('results/collisioncalc.csv')
    pd.DataFrame(data=output).to_json('results/collisioncalc.json')
