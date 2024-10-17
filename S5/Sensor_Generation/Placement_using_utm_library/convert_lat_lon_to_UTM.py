import csv

import pandas as pd
import utm

if __name__ == "__main__":
    Sensors = []
    output = {"x": [], "y": []}
    with open("sensors_latlon.csv", newline='') as csvfile:
        data = list(csv.reader(csvfile))
        for curr in data:
            try:
                Sensors.append([float(curr[0]), float(curr[1])])
            except:
                pass
    for sens in Sensors:
        latlon = utm.from_latlon(sens[0], sens[1])
        output['x'].append(latlon[0])
        output['y'].append(latlon[1])
    print(output)
    pd.DataFrame(data=output).to_csv('sensors_UTM.csv', index=False, header=False)
    pd.DataFrame(data=output).to_json('sensors_UTM.json')
