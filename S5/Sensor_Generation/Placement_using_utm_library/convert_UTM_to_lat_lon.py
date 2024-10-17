import csv
import os
from glob import glob
import pandas as pd
import utm

if __name__ == "__main__":
    source_folder = "sensors"
    output_folder = "results"
    dirname = os.path.dirname(__file__)
    inputpath = os.path.join(dirname, source_folder)
    sensor_files = "sensors_*.csv"
    sensor_data_paths = [file
                         for path, subdir, files in os.walk(inputpath)
                         for file in glob(os.path.join(path, sensor_files))]
    print(sensor_data_paths)
    for ind,currfile in enumerate(sensor_data_paths):
        name=currfile.split("_")[-1].split(".")[-2]
        print(name)
        Sensors = []
        output = {"lon": [], "lat": []}
        with open(currfile, newline='') as csvfile:
            data = list(csv.reader(csvfile))
            for curr in data:
                try:
                    Sensors.append([float(curr[0]), float(curr[1])])
                except:
                    pass
        for sens in Sensors:
            latlon = utm.to_latlon(sens[0], sens[1], 32, "U")
            output['lat'].append(latlon[1])
            output['lon'].append(latlon[0])
        print(output)
        pd.DataFrame(data=output).to_csv('sensors/latlon/sensors_'+str(name)+'_latlon.csv', index=False, header=False)
        pd.DataFrame(data=output).to_json('sensors/latlon/sensors_'+str(name)+'_latlon.json')
