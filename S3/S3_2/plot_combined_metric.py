import json
import math

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

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


def plot_run(filepath, color, label):
    global min_retries, min_wait, max_retries, max_wait
    results = []
    with open(filepath, newline='') as jsonfile:
        data = json.load(jsonfile)
        for curr in range(len(data["LBT_retries"])):
            all_runs = []
            all_runs_wait_time = []
            all_runs.append(data["LBT_retries"][curr])
            all_runs_wait_time.append(np.mean(data["LBT_total_wait_time"][curr]))
            results.append([data["placement_base_scenario"][curr], data["variable_value"][curr], np.average(all_runs),
                            np.average(all_runs_wait_time)])
        unique_placements = sorted(list(dict.fromkeys(data["placement_base_scenario"])), reverse=True)
        toplot = [[] for i in unique_placements]
        xaxis = []
        for i in unique_placements:
            xaxis.append(i)
            # xaxis.append(list(filter(lambda x: x[0] == i, translation_table))[0][1])
        for ind, placement in enumerate(unique_placements):
            min_retries = float("inf")
            min_wait = float("inf")
            max_retries = 0
            max_wait = 0
            update_min_max_overall(data, placement)
            res = []
            locations = []
            for curr in results:
                if curr[1] > 25:
                    if (curr[0] == placement):
                        res.append([curr[1], ((((curr[2] - min_retries) / (max_retries - min_retries)) + (
                                (curr[3] - min_wait) / (max_wait - min_wait))) / 2)])
                        locations.append(curr[1])
            best_overall = min(res, key=lambda k: k[1])
            results_entry = list(filter(lambda x: x[1] == best_overall[0], results))[0]
            toplot[ind] = [xaxis[ind], results_entry[1]]
        toplot = sorted(toplot, key=lambda x: x[0])
        toexport = {"placement_base_scenario": [], "results": []}
        for curr in range(len(toplot)):
            toexport["placement_base_scenario"].append(toplot[curr][0])
            toexport["results"].append(toplot[curr][1])
        with open("results.json", "w") as outfile:
            outfile.write(json.dumps(toexport))
        xaxis = [i[0] for i in toplot]
        toplot = [i[1] for i in toplot]
        print(xaxis)
        print(toplot)
        plt.plot(xaxis, toplot, color=color, label=label,lw=2.5)
        for i in [1941.9923947853897, 2338.2990470496998, 2815.480868058583, 3390.042231084836, 3606.5278015256044,
                  4342.519849258998]:
            plt.axvline(i / 2, color="red")


def update_min_max_overall(data, placement_base_scenario):
    global min_retries, min_wait, max_retries, max_wait
    results = []
    for curr in range(len(data["LBT_retries"])):
        all_runs = []
        all_runs_wait_time = []
        all_runs.append(data["LBT_retries"][curr])
        all_runs_wait_time.append(np.mean(data["LBT_total_wait_time"][curr]))
        if data["placement_base_scenario"][curr] == placement_base_scenario:
            if (data["variable_value"][curr] > 25):
                results.append(
                    [data["placement_base_scenario"][curr], data["variable_value"][curr], np.average(all_runs),
                     np.average(all_runs_wait_time)])
    min_retries = min(min(results, key=lambda k: k[2])[2], min_retries)
    min_wait = min(min(results, key=lambda k: k[3])[3], min_wait)
    max_retries = max(max(results, key=lambda k: k[2])[2], max_retries)
    max_wait = max(max(results, key=lambda k: k[3])[3], max_wait)


def plot_one_result(dataset, plot_file_name):
    plt.rcParams.update({'font.size': 26})
    plt.rcParams['figure.figsize'] = [10, 6]
    fig, ax = plt.subplots()
    colors = plt.cm.copper(np.linspace(0, 1, 5))
    plot_run(dataset, colors[0], "")
    # ax.set_xticks(np.arange(len(unique_base_scenarios)), labels=unique_base_scenarios)
    # ax.set_yticks(np.arange(len(unique_variable_parameters)), labels=unique_variable_parameters)
    ax.grid(which='major', alpha=0.2)
    # plt.legend(loc="lower right", ncol=2, bbox_to_anchor=(1.1, 1),
    #           fontsize=13)  # , handleheight=0.9, labelspacing=0.2, handlelength=0.7,fontsize=13)#,
    plt.gcf().subplots_adjust(bottom=0.19)
    plt.gcf().subplots_adjust(left=0.18)
    plt.gcf().subplots_adjust(top=0.9)
    # plt.xlabel('ToA Mean [ms]')
    plt.xlabel('Maximum node distance [m]')
    plt.ylabel('$L$ value with best $M_c$ [ms]')
    # plt.show()
    plt.savefig(plot_file_name)
    plt.close()


def plot_two_results(dataset, dataset_2, plot_file_name, label1, label2):
    plt.rcParams.update({'font.size': 28})
    plt.rcParams['figure.figsize'] = [10, 6]
    fig, ax = plt.subplots()
    colors = plt.cm.copper(np.linspace(0, 1, 5))
    plot_run(dataset, colors[0], label1)
    plot_run(dataset_2, colors[3], label2)
    # ax.set_xticks(np.arange(len(unique_base_scenarios)), labels=unique_base_scenarios)
    # ax.set_yticks(np.arange(len(unique_variable_parameters)), labels=unique_variable_parameters)
    ax.grid(which='major', alpha=0.2)
    leg = fig.legend(loc="upper left",
               bbox_to_anchor=(0.19, 0.89))
    for line in leg.get_lines():
        line.set_linewidth(4.0)
    plt.gcf().subplots_adjust(bottom=0.19)
    plt.gcf().subplots_adjust(left=0.18)
    plt.gcf().subplots_adjust(top=0.9)
    # plt.xlabel('ToA Mean [ms]')
    plt.xlabel('Maximum distance [m]')
    plt.ylabel('$L$ value with best $M_c$ [ms]')
    # plt.show()
    plt.savefig(plot_file_name)
    plt.close()


plot_two_results("./results/collision_probability/collision_probability_700_sensors.json",
                 "./results/collision_probability/collision_probability_1000_sensors.json",
                 "S3_2_Combined_Metric_combined.pdf", "700 end devices", "1000 end devices")
plot_one_result("./results/collision_probability/collision_probability_500_sensors.json",
                "S3_2_Combined_Metric_500.pdf")
plot_one_result("./results/collision_probability/collision_probability_700_sensors.json",
                "S3_2_Combined_Metric_700.pdf")
plot_one_result("./results/collision_probability/collision_probability_1500_sensors.json",
                "S3_2_Combined_Metric_1500.pdf")
plot_one_result("./results/collision_probability/collision_probability_1000_sensors.json",
                "S3_2_Combined_Metric_1000.pdf")
