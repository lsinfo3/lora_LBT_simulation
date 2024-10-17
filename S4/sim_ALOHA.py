import json
import math
import os
import random
import sys
from glob import glob
from multiprocessing import Pool

import utm
import numpy as np
from interlap import InterLap


def calculateDistance(x1, x2, y1, y2):
    return math.sqrt(math.pow(x1 - x2, 2) + math.pow(y1 - y2, 2))


def hata(gw_height, sf):
    sens_height = 1
    # represents Spreading Factor Tolerances for Path Loss in dB
    plrange = [131, 134, 137, 140, 141, 144]
    distance = 10 ** (-(69.55 + 76.872985 - 13.82 * math.log10(gw_height) - 3.2 * (math.log10(
        11.75 * sens_height) ** 2) + 4.97 - plrange[sf - 7]) / (44.9 - 6.55 * math.log10(gw_height)))
    return distance * 1000


def check_LBT_hidden_node(data, band, invalid, transmission_to_check):
    # Calculates, if any LBT transmission is scheduled on the current band, but unable to hear the transmission_to_check
    # Returns False if all LBT Transmission can hear the current sensor. Returns True if the hidden node problem occurs.
    coords_other_sensor = utm.from_latlon(data["lat"][str(transmission_to_check[2]["id"])],
                                          data["lon"][str(transmission_to_check[2]["id"])])
    overlapping_transmissions = list(band.find(
        [transmission_to_check[0], transmission_to_check[1]]))
    LBT_transmissions_to_check = []
    hidden_node_present = False
    for curr in overlapping_transmissions:
        if (curr[2]["type"] == "LBT"):
            LBT_transmissions_to_check.append(curr)
    for curr_transmission in LBT_transmissions_to_check:
        coords_this_sensor = utm.from_latlon(data["lat"][str(curr_transmission[2]["id"])],
                                             data["lon"][str(curr_transmission[2]["id"])])
        if calculateDistance(coords_this_sensor[0], coords_other_sensor[0], coords_this_sensor[1],
                             coords_other_sensor[1]) > hata(15, int(data["SF"][str(curr_transmission[2]["id"])])) and \
                transmission_to_check[2]["id"] != curr_transmission[2]["id"] and not invalid[
            int(curr_transmission[2]["index"])]:
            hidden_node_present = True
    return hidden_node_present

def check_LBT_violation_and_process(band, transmission, invalid, transmission_index, LBT_sens_period, LBT_max_retries,
                                    LBT_backoff_max_time, data, next_hour_transmissions):
    overlapping_transmissions = list(band.find([transmission[0] - LBT_sens_period, transmission[0]]))
    band_active = False
    coords_other_sensor = utm.from_latlon(data["lat"][str(transmission[2]["id"])],
                                          data["lon"][str(transmission[2]["id"])])
    for overlapping_transmission in overlapping_transmissions:
        coords_this_sensor = utm.from_latlon(data["lat"][str(transmission[2]["id"])],
                                             data["lon"][str(transmission[2]["id"])])
        for sf in range(6):
            if overlapping_transmission[2]["id"] in \
                    data["sf_collisions"][str(transmission[2]["id"])][sf] and overlapping_transmission[2]["id"] != \
                    transmission[2]["id"] and not invalid[
                int(overlapping_transmission[2]["index"])] and \
                    calculateDistance(coords_this_sensor[0], coords_other_sensor[0], coords_this_sensor[1],
                                      coords_other_sensor[1]) <= hata(15,
                                                                      int(data["SF"][
                                                                              str(overlapping_transmission[2]["id"])])):
                band_active = True
    if band_active and (transmission[2]["try"] < LBT_max_retries):
        invalid[int(transmission[2]["index"])] = True
        backoff = random.randrange(LBT_backoff_max_time-25,LBT_backoff_max_time+25)
        this_transmission = [transmission[0] + backoff, transmission[1] + backoff,
                             {"type": "LBT", "id": str(transmission[2]["id"]), "index": transmission_index,
                              "try": int(transmission[2]["try"]) + 1,
                              "total_backoff": float(transmission[2]["total_backoff"]) + backoff}]
        band.add(this_transmission)
        if this_transmission[1] > 3600000:
            this_transmission = [transmission[0] + backoff - 3600000, transmission[1] + backoff - 3600000,
                                 {"type": "LBT", "id": str(transmission[2]["id"]), "index": transmission_index,
                                  "try": int(transmission[2]["try"]) + 1,
                                  "total_backoff": float(transmission[2]["total_backoff"]) + backoff}]
            next_hour_transmissions.append(this_transmission)
        transmission_index += 1
        invalid.append(False)
    return transmission_index


def simulate_collision(args):
    sensor_data_paths = args[6]
    with open(sensor_data_paths[args[0]], newline='') as jsonfile:
        data = json.load(jsonfile)
        data = generate_types(data, args[7], args[8])
    payload_bytes = args[1]
    sim_hours = args[2]
    LBT_backoff_max_time = args[3]  # ms
    LBT_sens_period = args[4]  # ms
    LBT_max_retries = sys.maxsize * 2 + 1
    runs = args[9]
    sim_results = [[] for i in range(runs)]
    retries = [[] for i in range(runs)]
    wait_duration = [[] for i in range(runs)]
    total_gw_duty_cycle = [[[] for i in range(sim_hours)] for j in range(runs)]
    for run in range(runs):
        next_hour_transmissions = []
        transmission_index = 0
        invalid = []
        for hour in range(sim_hours):
            gw_duty_cycle = [0 for i in range(len(data["id"]))]
            print(hour)
            transmissions = next_hour_transmissions
            next_hour_transmissions = []
            band = InterLap()
            for trans in transmissions:
                band.add(trans)
            packet_types = ["ALOHA", "LBT"]
            collisions = [0 for i in packet_types]
            # Generate Transmissions
            for i in range(len(data["id"])):
                payload_bytes = random.randrange(1, 51)
                if data["channel_access"][i] == "ALOHA":
                    # ALOHA transmissions do not respect any other transmissions, thus the start time is random
                    sensor_sf = int(data["SF"][str(i)])
                    transmission_time_sens = payload_size_to_time(payload_bytes, sensor_sf)
                    start_time = random.randrange(0, 3600000)
                    this_transmission = [start_time, start_time + transmission_time_sens,
                                         {"type": "ALOHA", "id": data["id"][str(i)], "index": transmission_index}]
                    band.add(this_transmission)
                    transmissions.append(this_transmission)
                    if this_transmission[1] > 3600000:
                        this_transmission = [start_time - 3600000, start_time + transmission_time_sens - 3600000,
                                             {"type": "ALOHA", "id": data["id"][str(i)], "index": transmission_index}]
                        next_hour_transmissions.append(this_transmission)
                    transmission_index += 1
                    invalid.append(False)
                elif data["channel_access"][i] == "LBT":
                    # This is not actually the logic for LBT but rather the initial data packet.
                    # The only difference to ALOHA is the flag for the packet type and different list
                    sensor_sf = int(data["SF"][str(i)])
                    transmission_time_sens = payload_size_to_time(payload_bytes, sensor_sf)
                    start_time = random.randrange(0, 3600000)
                    this_transmission = [start_time, start_time + transmission_time_sens,
                                         {"type": "LBT", "id": data["id"][str(i)], "index": transmission_index,
                                          "try": 0, "total_backoff": 0}]
                    band.add(this_transmission)
                    transmissions.append(this_transmission)
                    if this_transmission[1] > 3600000:
                        this_transmission = [start_time - 3600000, start_time + transmission_time_sens - 3600000,
                                             {"type": "LBT", "id": data["id"][str(i)], "index": transmission_index,
                                              "try": 0, "total_backoff": 0}]
                        next_hour_transmissions.append(this_transmission)
                    transmission_index += 1
                    invalid.append(False)
            for curr_transmission in band:
                if not invalid[int(curr_transmission[2]["index"])]:
                    if curr_transmission[2]["type"] == "LBT":
                        transmission_index = check_LBT_violation_and_process(band, curr_transmission, invalid,
                                                                             transmission_index, LBT_sens_period,
                                                                             LBT_max_retries, LBT_backoff_max_time,
                                                                             data,
                                                                             next_hour_transmissions)
            # Check Transmissions for Overlap
            for curr_transmission in band:
                if not invalid[int(curr_transmission[2]["index"])]:
                    overlapping_transmissions = list(band.find(curr_transmission))
                    band_active = False
                    for overlapping_transmission in overlapping_transmissions:
                        for sf in range(6):
                            if overlapping_transmission[2]["id"] in \
                                    data["sf_collisions"][str(curr_transmission[2]["id"])][
                                        sf] and overlapping_transmission[2]["id"] != curr_transmission[2]["id"] and not \
                                    invalid[
                                        int(overlapping_transmission[2]["index"])] and not invalid[
                                int(curr_transmission[2]["index"])]:
                                band_active = True
                    if band_active:
                        collisions[packet_types.index(curr_transmission[2]["type"])] += 1
                    if (curr_transmission[2]["type"] == "LBT"):
                        retries[run].append(curr_transmission[2]["try"])
                        wait_duration[run].append(curr_transmission[2]["total_backoff"])
            non_invalid_transmissions = 0
            for i in list(band):
                if not invalid[int(i[2]["index"])]:
                    non_invalid_transmissions += 1
            sim_results[run].append(sum(collisions) / non_invalid_transmissions)

            for ind, val in enumerate(gw_duty_cycle):
                if val > 0:
                    total_gw_duty_cycle[run][hour].append([ind, val / 3600000])
            if len(total_gw_duty_cycle[run][hour]) == 0:
                total_gw_duty_cycle[run][hour].append([-1, 0])
    toexport = {"placement_base_scenario": [args[13]], "variable_value": [args[14]], "results": [sim_results],
                "GW_duty_cycle": [total_gw_duty_cycle], "LBT_retries": [[[np.average(i)] for i in retries]],
                "LBT_total_wait_time": [[np.average(i)] for i in wait_duration]}
    with open(str(args[-1]) + "/collision_probability_" + str(args[-3]) + "_" + str(args[-2]) + ".json",
              "w") as outfile:
        outfile.write(json.dumps(toexport))
    return [sim_results, total_gw_duty_cycle, [[np.average(i)] for i in retries], [[np.average(i)] for i in wait_duration]]


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


def generate_types(data, distribution, names):
    transmission_type = {"channel_access": [names[0] for i in range(len(data["id"]))]}
    for i in range(len(data["id"])):
        this_id = random.randrange(0, sum(distribution))
        step = sum(distribution)
        for curr in range(len(distribution) - 1, 0, -1):
            step -= distribution[curr]
            if this_id <= step:
                transmission_type["channel_access"][i] = names[curr]
    data.update(transmission_type)
    return data


if __name__ == '__main__':
    # Base parameters
    runs = 30
    payload_bytes = 51
    sim_hours = 24
    LBT_backoff_max_time = 29  # ms
    LBT_sens_period = 1  # ms
    LBT_max_retries = sys.maxsize * 2 + 1
    type_distribution = [10]
    types = ["ALOHA"]
    num_threads = 15
    # End of base parameters
    source_folder = "results/collisioncalc"
    split_pattern = "_RES"
    output_folder = "results/collision_probability"
    dirname = os.path.dirname(__file__)
    inputpath = os.path.join(dirname, source_folder)
    sensor_files = "collisioncalc_*.json"
    sensor_data_paths = [file
                         for path, subdir, files in os.walk(inputpath)
                         for file in glob(os.path.join(path, sensor_files))]
    sensor_data_paths = sorted(sensor_data_paths,key = lambda x: int(str(str(x).split(split_pattern)[1]).split(".json")[0]))
    sensor_values = [str(curr).split(split_pattern)[1] for curr in sensor_data_paths]
    sensor_values = [int(str(curr).split(".json")[0]) for curr in sensor_values]
    print(sensor_values)
    collision_probability = []
    results = []
    # Define Scenarios here: Replace parameter to be studied with variable_parameter and use the index of the
    # scenario in the "toexport" definition
    scenarios = []
    scenario_sensor_values = []
    variable_key = []
    with open("results_1000.json", newline='') as jsonfile:
        data = json.load(jsonfile)
    print(data)
    parameters = []
    for sens_value in sensor_values:
        mindist=float("inf")
        best_data=[]
        for curr in range(len(data['placement_base_scenario'])):
            dist=abs(sens_value-int(data['placement_base_scenario'][curr]))
            if(dist<mindist):
                mindist=dist
                best_data=[data['placement_base_scenario'][curr],data['results'][curr]]
        print([sens_value,best_data])
        parameters.append(best_data[1])
    for data in range(len(sensor_data_paths)):
        variable_parameter = parameters[data]
        scenarios.append(
            [data, payload_bytes, sim_hours, variable_parameter, LBT_sens_period, runs,
                sensor_data_paths, type_distribution, types, sensor_values[data], variable_parameter, output_folder])
        scenario_sensor_values.append(sensor_values[data])
        variable_key.append(variable_parameter)
    # End of scenario definition
    with Pool(num_threads) as p:
        results = p.map(simulate_collision, [i for i in scenarios])
    toexport = {"placement_base_scenario": [], "variable_value": [], "results": [], "GW_duty_cycle": [],
                "LBT_retries": [],
                "LBT_total_wait_time": []}
    for curr in range(len(scenarios)):
        toexport["placement_base_scenario"].append(scenario_sensor_values[curr])
        toexport["variable_value"].append(variable_key[curr])
        toexport["results"].append(results[curr][0])
        toexport["GW_duty_cycle"].append(results[curr][1])
        toexport["LBT_retries"].append(results[curr][2])
        toexport["LBT_total_wait_time"].append(results[curr][3])
    with open(str(output_folder) + "/collision_probability.json", "w") as outfile:
        outfile.write(json.dumps(toexport))
    # for currfile in range(len(sensor_data_paths)):
    #    with open(sensor_data_paths[currfile], newline='') as jsonfile:
    #        data = json.load(jsonfile)
    #        data = generate_types(data, [20], ["Scheduled"])
    #    results.append([sensor_values[currfile], simulate_collision(data)])
    #    print(results[-1])
    # with open(str(output_folder) + "/distance.json", "w") as outfile:
    #    outfile.write(json.dumps(results))
