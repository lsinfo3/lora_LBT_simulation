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


def calculate_clock_drift(last_sync_time, current_time, time_drift_per_hour):
    delta_time = current_time - last_sync_time
    delta_time_h = delta_time / 3600000
    return (delta_time_h * time_drift_per_hour)


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


def check_scheduled_violation_and_process(band, transmission, invalid, data, transmission_index,
                                          next_hour_transmissions, hour, scheduled_max_time_drift,
                                          scheduled_sync_packet_length, gw_duty_cycle):
    if calculate_clock_drift(data["last_sync"][int(transmission[2]["id"])],
                             hour * 3600000 + transmission[0],
                             int(data["time_drift_mode"][int(transmission[2]["id"])])) > scheduled_max_time_drift:
        overlapping_transmissions = list(band.find([transmission[1], transmission[1]]))
        band_active = False
        only_LBT = True
        for overlapping_transmission in overlapping_transmissions:
            for sf in range(6):
                if overlapping_transmission[2]["id"] in \
                        data["sf_collisions"][str(transmission[2]["id"])][sf] and overlapping_transmission[2]["id"] != \
                        transmission[2]["id"] and not invalid[int(overlapping_transmission[2]["index"])]:
                    band_active = True
                    if overlapping_transmission[2]["type"] != "LBT":
                        only_LBT = False
        if not band_active or (not check_LBT_hidden_node(data, band, invalid, transmission) and only_LBT):
            # successful sync generation
            gw_duty_cycle[int(data["BestGW"][str(transmission[2]["id"])])] += payload_size_to_time(
                scheduled_sync_packet_length, 12)
            sync_transmission = [transmission[1] + 1,
                                 transmission[1] + 1 + payload_size_to_time(scheduled_sync_packet_length,
                                                                            12),
                                 {"type": "Scheduled_Sync", "index": transmission_index,
                                  "id": data["id"][str(transmission[2]["id"])]}]
            band.add(sync_transmission)
            if sync_transmission[1] > 3600000:
                sync_transmission = [transmission[1] - 3600000,
                                     transmission[1] + payload_size_to_time(scheduled_sync_packet_length,
                                                                            data["SF"][str(
                                                                                transmission[2]["id"])]) - 3600000,
                                     {"type": "Scheduled_Sync", "index": transmission_index,
                                      "id": data["id"][str(transmission[2]["id"])]}]
                next_hour_transmissions.append(sync_transmission)
            transmission_index += 1
            invalid.append(False)

        else:
            # Transmission not received by Gateway, sync Transmission not generated
            pass
    return transmission_index


def check_scheduled_sync(band, transmission, invalid, hour, data):
    overlapping_transmissions = list(band.find([transmission[1], transmission[1]]))
    band_active = False
    for overlapping_transmission in overlapping_transmissions:
        for sf in range(6):
            if overlapping_transmission[2]["id"] in \
                    data["sf_collisions"][str(transmission[2]["id"])][sf] and overlapping_transmission[2]["id"] != \
                    transmission[2]["id"] and not invalid[int(overlapping_transmission[2]["index"])]:
                band_active = True
    if not band_active:
        # successful sync
        data["last_sync"][int(transmission[2]["id"])] = hour * 3600000 + transmission[1]


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
        backoff = random.randrange(LBT_backoff_max_time[0]-LBT_backoff_max_time[1],LBT_backoff_max_time[0]+LBT_backoff_max_time[1])
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
    sensor_data_paths = args[10]
    with open(sensor_data_paths[args[0]], newline='') as jsonfile:
        data = json.load(jsonfile)
        data = generate_types(data, args[11], args[12])
    payload_bytes = args[1]
    sim_hours = args[2]
    scheduled_buffer = args[3]  # ms
    scheduled_max_time_drift = args[4]  # ms
    scheduled_sync_packet_length = args[5]  # Byte
    scheduled_slot_length = args[6]  # Byte
    LBT_backoff_max_time = args[7]  # ms
    LBT_sens_period = args[8]  # ms
    LBT_max_retries = sys.maxsize * 2 + 1
    runs = args[9]
    sim_results = [[] for i in range(runs)]
    retries = [[] for i in range(runs)]
    wait_duration = [[] for i in range(runs)]
    total_gw_duty_cycle = [[[] for i in range(sim_hours)] for j in range(runs)]
    for run in range(runs):
        scheduled_slots = int(3600000 / (scheduled_slot_length))
        scheduled_required_slots = 0
        for i in range(len(data["id"])):
            if data["channel_access"][i] == "Scheduled":
                scheduled_required_slots += 1
        slot_assignment = []
        while len(slot_assignment) < scheduled_required_slots:
            slot_assignment.extend(random.sample(range(0, scheduled_slots), scheduled_slots))
        current_slot = 0
        data.update({"scheduled_slot": [-1 for i in data["id"]]})
        for i in range(len(data["id"])):
            if data["channel_access"][i] == "Scheduled":
                data["scheduled_slot"][i] = slot_assignment[current_slot]
                current_slot += 1
        next_hour_transmissions = []
        data.update({"last_sync": [0 for i in data["id"]]})
        data.update({"time_drift_mode": [random.randrange(2, 101) * 3600000 * 1e-6 for i in data["id"]]})
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
            packet_types = ["ALOHA", "Scheduled", "LBT", "Scheduled_Sync"]
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
                elif data["channel_access"][i] == "Scheduled":
                    # Scheduled sensors respect other scheduled sensors. In this scenario, all scheduled sensors occupy
                    # the beginning of the band with a specific guard time
                    sensor_sf = int(data["SF"][str(i)])
                    transmission_time_sens = payload_size_to_time(payload_bytes, sensor_sf)
                    start_time = (data["scheduled_slot"][i] * scheduled_slot_length)
                    time_drift = calculate_clock_drift(int(data["last_sync"][int(i)]),
                                                       start_time + hour * 3600000,
                                                       int(data["time_drift_mode"][int(i)]))
                    if hour == 0:
                        time_drift = random.randrange(
                            int(scheduled_slot_length - transmission_time_sens),
                            int(scheduled_slot_length))
                    this_transmission = [int(start_time + time_drift),
                                         int(start_time + transmission_time_sens + time_drift),
                                         {"type": "Scheduled", "id": data["id"][str(i)], "index": transmission_index}]
                    band.add(this_transmission)
                    transmissions.append(this_transmission)
                    if this_transmission[1] > 3600000:
                        this_transmission = [int(start_time + time_drift - 3600000),
                                             int(start_time + time_drift + transmission_time_sens - 3600000),
                                             {"type": "Scheduled", "id": data["id"][str(i)],
                                              "index": transmission_index}]
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
                    if curr_transmission[2]["type"] == "Scheduled":
                        transmission_index = check_scheduled_violation_and_process(band, curr_transmission, invalid,
                                                                                   data, transmission_index,
                                                                                   next_hour_transmissions, hour,
                                                                                   scheduled_max_time_drift,
                                                                                   scheduled_sync_packet_length,
                                                                                   gw_duty_cycle)
                    if curr_transmission[2]["type"] == "Scheduled_Sync":
                        check_scheduled_sync(band, curr_transmission, invalid, hour, data)
                    elif curr_transmission[2]["type"] == "LBT":
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
                "GW_duty_cycle": [total_gw_duty_cycle], "LBT_retries": [retries],
                "LBT_total_wait_time": [wait_duration]}
    with open(str(args[15]) + "/temp/collision_probability_" + str(args[13]) + "_" + str(args[14]) + ".json",
              "w") as outfile:
        outfile.write(json.dumps(toexport))
    return [sim_results, total_gw_duty_cycle, retries, wait_duration]


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
    for variable_parameter2 in range(25, 1110,25):
        # Base parameters
        runs = 30
        payload_bytes = 51
        sim_hours = 24
        scheduled_sync_packet_length = 6  # Byte
        scheduled_buffer = 11.1 * 360 + 36 + payload_size_to_time(scheduled_sync_packet_length, 12)  # ms # mit k aus figure_6_data02_slotted_RA_lesstraffic
        scheduled_max_time_drift = 3980  # ms
        scheduled_slot_length = payload_size_to_time(51, 12) + scheduled_buffer  # Byte
        LBT_backoff_max_time = 29  # ms
        LBT_sens_period = 1  # ms
        LBT_max_retries = sys.maxsize * 2 + 1
        type_distribution = [10]
        types = ["LBT"]
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
        # for variable_parameter in range(800, 1201,10):
        for variable_parameter in range(1100, 1130,10):
                for data in range(len(sensor_data_paths)):
                    scenarios.append(
                        [data, payload_bytes, sim_hours, scheduled_buffer, scheduled_max_time_drift,
                        scheduled_sync_packet_length, scheduled_slot_length, [variable_parameter,variable_parameter2], LBT_sens_period, runs,
                        sensor_data_paths, type_distribution, types, sensor_values[data], [variable_parameter,variable_parameter2], output_folder])
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
        with open(str(output_folder) + "/collision_probability"+str(variable_parameter2)+".json", "w") as outfile:
            outfile.write(json.dumps(toexport))
        # for currfile in range(len(sensor_data_paths)):
        #    with open(sensor_data_paths[currfile], newline='') as jsonfile:
        #        data = json.load(jsonfile)
        #        data = generate_types(data, [20], ["Scheduled"])
        #    results.append([sensor_values[currfile], simulate_collision(data)])
        #    print(results[-1])
        # with open(str(output_folder) + "/distance.json", "w") as outfile:
        #    outfile.write(json.dumps(results))
