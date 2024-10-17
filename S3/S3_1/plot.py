import json
import math

import matplotlib
import matplotlib.pyplot as plt
import numpy as np


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


def plot_run(filepath, mycolor, mylabel):
    results = []
    with open(filepath, newline='') as jsonfile:
        data = json.load(jsonfile)
        for curr in range(len(data["results"])):
            all_runs = []
            for run in range(len(data["results"][curr])):
                for hour in range(5, 24):
                    all_runs.append(data["results"][curr][run][hour])
            results.append([data["placement_base_scenario"][curr], data["variable_value"][curr], all_runs])
        unique_base_scenarios = sorted(list(dict.fromkeys(data["placement_base_scenario"])))
        unique_variable_parameters = sorted(list(dict.fromkeys(data["variable_value"])), reverse=True)
        toplot = [[0] * len(unique_variable_parameters) for i in unique_base_scenarios]
        for res in results:
            toplot[unique_base_scenarios.index(res[0])][unique_variable_parameters.index(res[1])] = res[2]
    plt.plot(unique_variable_parameters, calculate_quantile(toplot[0], 0.95), ':', color=mycolor)
    plt.plot(unique_variable_parameters, calculate_quantile(toplot[0], 0.5), color=mycolor, label=mylabel)
    plt.plot(unique_variable_parameters, calculate_quantile(toplot[0], 0.05), ':', color=mycolor)


def plot_LBT_retries(filepath, mycolor, mylabel, ax):
    results = []
    with open(filepath, newline='') as jsonfile:
        data = json.load(jsonfile)
        for curr in range(len(data["LBT_retries"])):
            all_runs = []
            for run in range(len(data["LBT_retries"][curr])):
                all_runs.append(sum(data["LBT_retries"][curr][run]) / len(data["LBT_retries"][curr][run]))
            results.append([data["placement_base_scenario"][curr], data["variable_value"][curr], all_runs])
        unique_base_scenarios = sorted(list(dict.fromkeys(data["placement_base_scenario"])))
        unique_variable_parameters = sorted(list(dict.fromkeys(data["variable_value"])), reverse=True)
        toplot = [[0] * len(unique_variable_parameters) for i in unique_base_scenarios]
        for res in results:
            toplot[unique_base_scenarios.index(res[0])][unique_variable_parameters.index(res[1])] = res[2]
    print(toplot[0])
    ax.plot(unique_variable_parameters, calculate_quantile(toplot[0], 0.95), ':', color=mycolor)
    ax.plot(unique_variable_parameters, calculate_quantile(toplot[0], 0.5), color=mycolor, label=mylabel)
    ax.plot(unique_variable_parameters, calculate_quantile(toplot[0], 0.05), ':', color=mycolor)


def plot_LBT_wait_times(filepath, mycolor, mylabel, ax):
    results = []
    with open(filepath, newline='') as jsonfile:
        data = json.load(jsonfile)
        for curr in range(len(data["LBT_total_wait_time"])):
            all_runs = []
            for run in range(len(data["LBT_total_wait_time"][curr])):
                all_runs.append(np.mean(data["LBT_total_wait_time"][curr][run]))
            results.append([data["placement_base_scenario"][curr], data["variable_value"][curr], all_runs])
        unique_base_scenarios = sorted(list(dict.fromkeys(data["placement_base_scenario"])))
        unique_variable_parameters = sorted(list(dict.fromkeys(data["variable_value"])), reverse=True)
        toplot = [[0] * len(unique_variable_parameters) for i in unique_base_scenarios]
        for res in results:
            toplot[unique_base_scenarios.index(res[0])][unique_variable_parameters.index(res[1])] = res[2]
    print(toplot[0])
    ax.plot(unique_variable_parameters, calculate_quantile(toplot[0], 0.95), ':', color=mycolor)
    ax.plot(unique_variable_parameters, calculate_quantile(toplot[0], 0.5), color=mycolor, label=mylabel)
    ax.plot(unique_variable_parameters, calculate_quantile(toplot[0], 0.05), ':', color=mycolor)

plt.rcParams.update({'font.size': 16})
plt.figure(1, figsize=(10, 6))
fig, ax = plt.subplots()
Scenarios = range(25, 890,25)
ax2 = ax.twinx()
colors = plt.cm.copper(np.linspace(0, 1, len(Scenarios)+1))
out_LBT = "S3_1.pdf"
for ind, Scenario in enumerate(Scenarios):
    dataset = "./results/collision_probability/collision_probability" + str(Scenario) + ".json"
    plot_LBT_wait_times(dataset, colors[ind], "Wait Time", ax)
    plot_LBT_retries(dataset, colors[ind+1], "Transmission Attempts", ax2)
# ax.set_xticks(np.arange(len(unique_base_scenarios)), labels=unique_base_scenarios)
# ax.set_yticks(np.arange(len(unique_variable_parameters)), labels=unique_variable_parameters)
plt.grid(which='major')
#fig.legend(loc="upper right", ncol=2,
#           fontsize=13)  # , handleheight=0.9, labelspacing=0.2, handlelength=0.7,fontsize=13)#,
plt.gcf().subplots_adjust(bottom=0.19)
plt.gcf().subplots_adjust(left=0.18)
plt.gcf().subplots_adjust(right=0.85)
plt.gcf().subplots_adjust(top=0.85)
ax.set_xlabel('Backoff Time [ms]')
ax.set_ylabel('Wait Time [ms]')
ax2.set_ylabel('Transmission Attempts [#]')
# plt.show()
plt.savefig(out_LBT)
plt.close()
