import csv
import math
from multiprocessing import Pool

from glob import glob
import os
import numpy as np
import pandas as pd
import utm


def calculateDistance(x1, x2, y1, y2):
    return math.sqrt(math.pow(x1 - x2, 2) + math.pow(y1 - y2, 2))


def generateEdges(nodes, Max_Range, Max_Sensors):
    edges = [[] for i in nodes]
    previous_covered = 0
    for curr_sensor in nodes:
        if (int((nodes.index(curr_sensor) / len(nodes) * 100)) > previous_covered):
            print("Placement: " + str(int((nodes.index(curr_sensor) / len(nodes) * 100))))
        curr_connected = 0
        for sensor_to_test in nodes:
            if (sensor_to_test != curr_sensor):
                if (calculateDistance(curr_sensor[0], sensor_to_test[0], curr_sensor[1],
                                      sensor_to_test[1]) <= Max_Range and curr_connected < Max_Sensors):
                    edges[nodes.index(curr_sensor)].append(nodes.index(sensor_to_test))
                    curr_connected += 1
    return (edges)


def hata(sf, gw_height, sens_height):  # returns distance in m
    # represents Spreading Factor Tolerances for Path Loss in dB
    plrange = [131, 134, 137, 140, 141, 144]
    distance = 10 ** (-(69.55 + 76.872985 - 13.82 * math.log10(gw_height) - 3.2 * (math.log10(
        11.75 * sens_height) ** 2) + 4.97 - plrange[sf - 7]) / (44.9 - 6.55 * math.log10(gw_height)))
    return distance * 1000


def create_placement(vars):
    Max_Range = vars[1]
    Sensors = vars[0]
    zonenumber = vars[4]
    print(Max_Range)
    Gateways = []
    Min_Sensors = vars[2]
    Max_Sensors = vars[3]
    name=vars[5]
    Target_Coverage = 100  # %
    oldsensors = [i for i in Sensors]
    while (100 - (len(oldsensors) / len(Sensors)) * 100 < Target_Coverage):
        edges = generateEdges(oldsensors, Max_Range, Max_Sensors)
        if (len(edges) < 1):
            break
        designatedgw = max(edges, key=len)
        if (len(designatedgw) < Min_Sensors):
            break
        Gateways.append(Sensors.index(oldsensors[edges.index(designatedgw)]))
        newsensors = []
        for curr_sensor in oldsensors:
            if (oldsensors.index(curr_sensor) != edges.index(designatedgw) and oldsensors.index(
                    curr_sensor) not in designatedgw):
                newsensors.append(curr_sensor)
        oldsensors = newsensors
    output = {"id": [], "x": [], "y": [], "height": [], "environment": []}
    for g in Gateways:
        latlon = utm.to_latlon(Sensors[g][0], Sensors[g][1], zonenumber[0], zonenumber[1], strict=False)
        output['id'].append(g)
        output['x'].append(latlon[1])
        output['y'].append(latlon[0])
        output['height'].append(5.0)
        output['environment'].append("urban")
    pd.DataFrame(data=output).to_csv('results/legacy_format/gateways_Placement_Range' + str(int(name)) + '.csv')
    Sensors_to_export = [[Sensors[i][0], Sensors[i][1], 0, 0, float("Inf"), 0] for i in range(len(Sensors))]
    for sens in Sensors_to_export:
        for g in Gateways:
            dist = calculateDistance(Sensors[g][0], sens[0], Sensors[g][1], sens[1])
            if (dist < sens[4]):
                sens[4] = dist
                sens[3] = g
                currsf = 12
                for sf in range(12, 6, -1):
                    if dist < hata(sf, 15, 1):
                        currsf = sf
                sens[2] = currsf
                sens[5] += 1
    output = {"lon": [], "lat": [], "BestGW": [], "SF": [], "NumberOfSensors": [], "NumGWs": []}
    for sens in Sensors_to_export:
        if (sens[2] != 0):
            latlon = utm.to_latlon(sens[0], sens[1], zonenumber[0], zonenumber[1], strict=False)
            output['lat'].append(latlon[0])
            output['lon'].append(latlon[1])
            output['BestGW'].append(sens[3])
            output['SF'].append(sens[2])
            output['NumberOfSensors'].append(1)
            output['NumGWs'].append(sens[5])
    pd.DataFrame(data=output).to_csv('results/legacy_format/reachable_sensors_Range' + str(int(name)) + '.csv')
    pd.DataFrame(data=output).to_json('results/legacy_format/reachable_sensors_Range' + str(int(name)) + '.json')
    output = {"lon": [], "lat": [], "BestGW": [], "SF": [], "NumberOfSensors": [], "NumGWs": [], "IsGateway": []}
    for sens in Sensors_to_export:
        if (sens[2] != 0):
            latlon = utm.to_latlon(sens[0], sens[1], zonenumber[0], zonenumber[1], strict=False)
            try:
                Gateways.index(Sensors_to_export.index(sens))
                gwflag = True
            except ValueError:
                gwflag = False
            output['lat'].append(latlon[0])
            output['lon'].append(latlon[1])
            output['BestGW'].append(sens[3])
            output['SF'].append(sens[2])
            output['NumberOfSensors'].append(1)
            output['NumGWs'].append(sens[5])
            output['IsGateway'].append(gwflag)
    pd.DataFrame(data=output).to_csv('results/placement_results' + str(int(name)) + '.csv')
    pd.DataFrame(data=output).to_json('results/placement_results' + str(int(name)) + '.json')
    #output = [[0.0 for i in range(len(Sensors))] for i in range(len(Sensors))]
    #for x in range(len(Sensors)):
    #    for y in range(len(Sensors)):
    #        if x != y:
    #            dist = calculateDistance(Sensors[x][0], Sensors[y][0], Sensors[x][1], Sensors[y][1])
    #            output[x][y] = dist
    #            output[y][x] = dist
    #pd.DataFrame(data=output).to_csv('results/distances.csv', header=None, index=None)
    #pd.DataFrame(data=output).to_json('results/distances.json')


if __name__ == "__main__":
    source_folder = "sensors/latlon"
    dirname = os.path.dirname(__file__)
    inputpath = os.path.join(dirname, source_folder)
    sensor_files = "sensors_*_latlon.csv"
    sensor_data_paths = [file
                         for path, subdir, files in os.walk(inputpath)
                         for file in glob(os.path.join(path, sensor_files))]
    print(sensor_data_paths)
    for currfile in sensor_data_paths:
        name=currfile.split("_")[-2]
        print(name)
        base_range = hata(12, 15, 1)
        lat = []
        lon = []
        Sensors = []
        with open(currfile, newline='') as csvfile:
            data = list(csv.reader(csvfile))
            for curr in data:
                try:
                    # Sensors.append([float(curr[0]), float(curr[1])])
                    lat.append(float(curr[0]))
                    lon.append(float(curr[1]))
                except:
                    pass
        tempsensors = utm.from_latlon(np.array(lat), np.array(lon))
        zonenumber = [tempsensors[2], tempsensors[3]]
        tempsensors = [tempsensors[0].tolist(), tempsensors[1].tolist()]
        for i in range(len(tempsensors[0])):
            Sensors.append([tempsensors[0][i], tempsensors[1][i]])
        print(zonenumber)
        configs = [i for i in range(300, 2601, 50)]
        # create_placement([Sensors, hata(8, 15, 1), 0, 750, zonenumber,name])
        with Pool(10) as p:
            devices_against_collision = p.map(create_placement, [[Sensors, i, 0, 1000, zonenumber,i] for i in configs])
