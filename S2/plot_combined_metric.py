import json
import math

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

colors = plt.cm.copper(np.linspace(0, 1, 5))
Scenario = "exponential"
dataset = "./results/collision_probability/" + Scenario + ".json"
out_LBT = Scenario + "_Combined_Metric.pdf"

min_retries = float("inf")
min_wait = float("inf")
max_retries = 0
max_wait = 0


def calculate_quantile(data, quantile):
    toreturn = []
    for i in data:
        sortedi = sorted(i)
        if not isinstance((len(i) * quantile) - 1, int):
            toreturn.append(sortedi[math.ceil((len(i) * quantile)) - 1])
        else:
            toreturn.append(
                0.5 * (sortedi[(len(i) * quantile)] + sortedi[(len(i) * quantile) + 1]))
    return toreturn


def plot_run(filepath, mycolor):
    global min_retries, min_wait, max_retries, max_wait
    results = []
    with open(filepath, newline='') as jsonfile:
        data = json.load(jsonfile)
        for curr in range(len(data["LBT_retries"])):
            all_runs = []
            all_runs_wait_time = []
            for run in range(len(data["LBT_retries"][curr])):
                all_runs.append(sum(data["LBT_retries"][curr][run]) / len(data["LBT_retries"][curr][run]))
                all_runs_wait_time.append(np.mean(data["LBT_total_wait_time"][curr][run]))
            results.append([data["placement_base_scenario"][curr], data["variable_value"][curr], np.average(all_runs),
                            np.average(all_runs_wait_time)])
        unique_variable_parameters = sorted(list(dict.fromkeys(data["variable_value"])), reverse=True)
        res = []
        locations = []
        for curr in results:
            res.append((((curr[2] - min_retries) / (max_retries - min_retries)) + (
                        (curr[3] - min_wait) / (max_wait - min_wait))) / 2)
            locations.append(curr[1])
        print(res)
    plt.plot(locations, [i*100 for i in res], color=mycolor,lw=2.5)


def update_min_max_overall(filepath):
    global min_retries, min_wait, max_retries, max_wait
    results = []
    with open(filepath, newline='') as jsonfile:
        data = json.load(jsonfile)
        for curr in range(len(data["LBT_retries"])):
            all_runs = []
            all_runs_wait_time = []
            for run in range(len(data["LBT_retries"][curr])):
                all_runs.append(sum(data["LBT_retries"][curr][run]) / len(data["LBT_retries"][curr][run]))
                all_runs_wait_time.append(np.mean(data["LBT_total_wait_time"][curr][run]))
            results.append([data["placement_base_scenario"][curr], data["variable_value"][curr], np.average(all_runs),
                            np.average(all_runs_wait_time)])
        min_retries = min(min(results, key=lambda k: k[2])[2], min_retries)
        min_wait = min(min(results, key=lambda k: k[3])[3], min_wait)
        max_retries = max(max(results, key=lambda k: k[2])[2], max_retries)
        max_wait = max(max(results, key=lambda k: k[3])[3], max_wait)
        print([min_retries, min_wait, max_retries, max_wait])


plt.rcParams.update({'font.size': 26})
plt.rcParams['figure.figsize'] = [10, 6]
fig, ax = plt.subplots()
update_min_max_overall(dataset)
plot_run(dataset, colors[0])
# ax.set_xticks(np.arange(len(unique_base_scenarios)), labels=unique_base_scenarios)
# ax.set_yticks(np.arange(len(unique_variable_parameters)), labels=unique_variable_parameters)
ax.grid(which='major', alpha=0.2)
# plt.legend(loc="lower right", ncol=2, bbox_to_anchor=(1.1, 1),
#           fontsize=13)  # , handleheight=0.9, labelspacing=0.2, handlelength=0.7,fontsize=13)#,
plt.gcf().subplots_adjust(bottom=0.19)
plt.gcf().subplots_adjust(left=0.18)
plt.gcf().subplots_adjust(right=0.85)
plt.gcf().subplots_adjust(top=0.9)
plt.xlabel(r'$\lambda$')
plt.ylabel(r'Combined metric $M_c$ [%]')
# plt.show()
plt.savefig(out_LBT)
plt.close()
