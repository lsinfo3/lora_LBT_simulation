import json
import math

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as st


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
                all_runs.append(np.mean(data["results"][curr][run]))
            results.append([data["placement_base_scenario"][curr], data["variable_value"][curr], all_runs])
        unique_base_scenarios = sorted(list(dict.fromkeys(data["placement_base_scenario"])))
        unique_variable_parameters = sorted(list(dict.fromkeys(data["variable_value"])), reverse=True)
        toplot = [0 for i in range(len(unique_base_scenarios))]
        for res in results:
            toplot[unique_base_scenarios.index(res[0])] = res[2]
    print(toplot[0])
    # ax.plot(unique_base_scenarios, calculate_quantile(toplot, 0.95), ':', color=mycolor)
    plt.plot(unique_base_scenarios, [np.mean(i)*100 for i in toplot], color=mycolor, label=mylabel,lw=2.5)
    # ax.plot(unique_variable_parameters, calculate_quantile(toplot[0], 0.05), ':', color=mycolor)
    confidence_interval = [st.t.interval(alpha=0.99, df=len(i) - 1, loc=np.mean(i), scale=st.sem(i)) for i in toplot]
    ax.fill_between(unique_base_scenarios, [np.percentile(i, 100)*100 for i in toplot],
                    [np.percentile(i, 0)*100 for i in toplot],
                    color=mycolor, alpha=0.5)


def plot_LBT_retries(filepath, mycolor, mylabel, ax):
    results = []
    with open(filepath, newline='') as jsonfile:
        data = json.load(jsonfile)
        for curr in range(len(data["LBT_retries"])):
            all_runs = []
            for run in range(len(data["LBT_retries"][curr])):
                all_runs.append(np.mean(data["LBT_retries"][curr][run]))
            results.append([data["placement_base_scenario"][curr], data["variable_value"][curr], all_runs])
        unique_base_scenarios = sorted(list(dict.fromkeys(data["placement_base_scenario"])))
        unique_variable_parameters = sorted(list(dict.fromkeys(data["variable_value"])), reverse=True)
        toplot = [0 for i in range(len(unique_base_scenarios))]
        for res in results:
            toplot[unique_base_scenarios.index(res[0])] = res[2]
    print("retries")
    print(toplot[0])
    print(max([np.max(i) for i in toplot]))
    plt.plot(unique_base_scenarios, [np.mean(i) for i in toplot], color=mycolor, label=mylabel,lw=2.5)
    # ax.plot(unique_variable_parameters, calculate_quantile(toplot[0], 0.05), ':', color=mycolor)
    confidence_interval = [st.t.interval(alpha=0.99, df=len(i) - 1, loc=np.mean(i), scale=st.sem(i)) for i in toplot]
    ax.fill_between(unique_base_scenarios, [i[1] for i in confidence_interval],
                    [i[0] for i in confidence_interval],
                    color=mycolor, alpha=0.5)


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
        toplot = [0 for i in range(len(unique_base_scenarios))]
        for res in results:
            toplot[unique_base_scenarios.index(res[0])] = res[2]
    print("delay")
    print(toplot[0])
    print(max([np.max(i) for i in toplot]))
    plt.plot(unique_base_scenarios, [np.mean(i) for i in toplot], color=mycolor, label=mylabel,lw=2.5)
    # ax.plot(unique_variable_parameters, calculate_quantile(toplot[0], 0.05), ':', color=mycolor)
    confidence_interval = [st.t.interval(alpha=0.99, df=len(i) - 1, loc=np.mean(i), scale=st.sem(i)) for i in toplot]
    ax.fill_between(unique_base_scenarios, [i[1] for i in confidence_interval],
                    [i[0] for i in confidence_interval],
                    color=mycolor, alpha=0.5)

plt.rcParams.update({'font.size': 26})
plt.rcParams['figure.figsize'] = [10, 6]
fig, ax = plt.subplots()
colors = plt.cm.copper(np.linspace(0, 1, 5))
Scenario = "LBT"
dataset = "./results/collision_probability/" + Scenario + ".json"
out_LBT = Scenario + ".pdf"
out_Collision_prob = Scenario + "_collision_prob.pdf"

plot_LBT_wait_times(dataset, colors[0], "Delay", ax)
ax2 = ax.twinx()
plot_LBT_retries(dataset, colors[3], "Retransmission\nattempts", ax2)
for i in [1941.9923947853897, 2338.2990470496998, 2815.480868058583, 3390.042231084836, 3606.5278015256044,4342.519849258998]:
    plt.axvline(i / 2, color="red")
# ax.set_xticks(np.arange(len(unique_base_scenarios)), labels=unique_base_scenarios)
# ax.set_yticks(np.arange(len(unique_variable_parameters)), labels=unique_variable_parameters)
ax.grid(which='major', alpha=0.2)
leg = fig.legend(loc="upper left",
           bbox_to_anchor=(0.19, 0.89))  # , handleheight=0.9, labelspacing=0.2, handlelength=0.7,fontsize=13)#,   # , handleheight=0.9, labelspacing=0.2, handlelength=0.7,fontsize=13)#,
for line in leg.get_lines():
    line.set_linewidth(4.0)
plt.gcf().subplots_adjust(bottom=0.19)
plt.gcf().subplots_adjust(left=0.18)
plt.gcf().subplots_adjust(right=0.85)
plt.gcf().subplots_adjust(top=0.9)
ax.set_xlabel('Range [m]')
ax.set_ylabel('Delay [ms]')
ax2.set_ylabel('Retransmission attempts')
# plt.show()
plt.savefig(out_LBT)
plt.close()

plt.rcParams.update({'font.size': 26})
plt.rcParams['figure.figsize'] = [10, 6]
fig, ax = plt.subplots()
Scenario = "ALOHA"
dataset = "./results/collision_probability/" + Scenario + ".json"
out_LBT = Scenario + ".pdf"
out_Collision_prob = Scenario + "_collision_prob.pdf"
plot_run(dataset, colors[0], "ALOHA")
Scenario = "LBT"
dataset = "./results/collision_probability/" + Scenario + ".json"
out_LBT = Scenario + ".pdf"
out_Collision_prob = Scenario + "_collision_prob.pdf"
plot_run(dataset, colors[3], "LBT")
for i in [1941.9923947853897, 2338.2990470496998, 2815.480868058583, 3390.042231084836, 3606.5278015256044,4342.519849258998]:
    plt.axvline(i / 2, color="red")
# ax.set_xticks(np.arange(len(unique_base_scenarios)), labels=unique_base_scenarios)
# ax.set_yticks(np.arange(len(unique_variable_parameters)), labels=unique_variable_parameters)
plt.grid(which='major')
leg = fig.legend(loc="upper left",
           bbox_to_anchor=(0.19, 0.89))  # , handleheight=0.9, labelspacing=0.2, handlelength=0.7,fontsize=13)#,   # , handleheight=0.9, labelspacing=0.2, handlelength=0.7,fontsize=13)#,
for line in leg.get_lines():
    line.set_linewidth(4.0)
plt.gcf().subplots_adjust(bottom=0.19)
plt.gcf().subplots_adjust(left=0.18)
plt.gcf().subplots_adjust(right=0.85)
plt.gcf().subplots_adjust(top=0.9)
plt.xlabel('Range [m]')
plt.ylabel('Collision probability [%]')
# plt.show()
plt.savefig(out_Collision_prob)
plt.close()
