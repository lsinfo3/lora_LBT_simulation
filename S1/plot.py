import json
import math

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as st
from scipy.stats import linregress
from scipy.optimize import curve_fit
from scipy.optimize import differential_evolution
import warnings

plt.rcParams.update({'font.size': 26})
plt.rcParams['figure.figsize'] = [10, 6]
fig, ax = plt.subplots()
colors = plt.cm.copper(np.linspace(0, 1, 5))
Scenario = "S2_1"
dataset = "./results/collision_probability/" + Scenario + ".json"
out_LBT = Scenario + ".pdf"
out_Collision_prob = Scenario + "_collision_prob.pdf"

def func(x, a, b, c):
    return a * np.exp(b * x) + c




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
                for hour in range(0, 24):
                    all_runs.append(data["results"][curr][run][hour])
            results.append([data["placement_base_scenario"][curr], data["variable_value"][curr], all_runs])
        unique_base_scenarios = sorted(list(dict.fromkeys(data["placement_base_scenario"])))
        unique_variable_parameters = sorted(list(dict.fromkeys(data["variable_value"])), reverse=True)
        toplot = [[0] * len(unique_variable_parameters) for i in unique_base_scenarios]
        for res in results:
            toplot[unique_base_scenarios.index(res[0])][unique_variable_parameters.index(res[1])] = res[2]
    # plt.plot(unique_variable_parameters, calculate_quantile(toplot[0], 0.95), ':', color=mycolor)
    plt.plot(unique_variable_parameters, [np.mean(i)*100 for i in toplot[0]], color=mycolor, label=mylabel,lw=2.5)
    # plt.plot(unique_variable_parameters, calculate_quantile(toplot[0], 0.05), ':', color=mycolor)
    confidence_interval = [st.t.interval(confidence=0.99, df=len(i) - 1, loc=np.mean(i)*100, scale=st.sem([j*100 for j in i])) for i in toplot[0]]
    print("p_coll")
    print(np.mean(toplot[0][unique_variable_parameters.index(1)]))
    print(confidence_interval[unique_variable_parameters.index(1)][1]-confidence_interval[unique_variable_parameters.index(1)][0])
    ax.fill_between(unique_variable_parameters, [i[1] for i in confidence_interval],
                    [i[0] for i in confidence_interval],
                    color=mycolor, alpha=0.5)


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
    print("retries")
    print(unique_variable_parameters)
    print([np.mean(i) for i in toplot[0]])
    #print(linregress(unique_variable_parameters,[np.mean(i) for i in toplot[0]]))
    #popt,pcov = curve_fit(func,unique_variable_parameters,[np.mean(i) for i in toplot[0]])
    #print(curve_fit(func,unique_variable_parameters,[np.mean(i) for i in toplot[0]]))
    #print(np.sqrt(np.diag(pcov)))
    # ax.plot(unique_variable_parameters, calculate_quantile(toplot[0], 0.95), ':', color=mycolor)
    plt.plot(unique_variable_parameters, [np.mean(i) for i in toplot[0]], color=mycolor, label=mylabel,lw=2.5)
    #m=linregress(unique_variable_parameters,[np.mean(i) for i in toplot[0]])
    #plt.plot(unique_variable_parameters,[m[0]*x+m[1] for x in unique_variable_parameters])
    # ax.plot(unique_variable_parameters, calculate_quantile(toplot[0], 0.05), ':', color=mycolor)
    confidence_interval = [st.t.interval(confidence=0.99, df=len(i) - 1, loc=np.mean(i), scale=st.sem(i)) for i in toplot[0]]
    ax.fill_between(unique_variable_parameters, [i[1] for i in confidence_interval],
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
        toplot = [[0] * len(unique_variable_parameters) for i in unique_base_scenarios]
        for res in results:
            toplot[unique_base_scenarios.index(res[0])][unique_variable_parameters.index(res[1])] = res[2]
    print("wait_time")
    print(unique_variable_parameters)
    print([np.mean(i) for i in toplot[0]])
    #print(linregress(unique_variable_parameters,[np.mean(i) for i in toplot[0]]))
    xData = np.array(unique_variable_parameters)
    yData = np.array([np.mean(i) for i in toplot[0]])
    def sumOfSquaredError(parameterTuple):
        warnings.filterwarnings("ignore") # do not print warnings by genetic algorithm
        val = func(xData, *parameterTuple)
        return np.sum((yData - val) ** 2.0)


    def generate_Initial_Parameters():
        minY = min(yData)
        maxY = max(yData)

        parameterBounds = []
        parameterBounds.append([0.0, 1000]) # search bounds for a
        parameterBounds.append([0, 150]) # search bounds for b
        parameterBounds.append([minY, maxY]) # search bounds for offset

        # "seed" the numpy random number generator for repeatable results
        result = differential_evolution(sumOfSquaredError, parameterBounds, seed=3)
        return result.x
        # by default, differential_evolution completes by calling curve_fit() using parameter bounds
    #geneticParameters = generate_Initial_Parameters()
    #popt,pcov = curve_fit(func,unique_variable_parameters,[np.mean(i) for i in toplot[0]],geneticParameters)
    #print(popt)
    #print(np.sqrt(np.diag(pcov)))
    # ax.plot(unique_variable_parameters, calculate_quantile(toplot[0], 0.95), ':', color=mycolor)
    plt.plot(unique_variable_parameters, [np.mean(i) for i in toplot[0]], color=mycolor, label=mylabel,lw=2.5)
    #plt.plot(unique_variable_parameters,[func(x,popt[0],popt[1],popt[2]) for x in unique_variable_parameters])
    # ax.plot(unique_variable_parameters, calculate_quantile(toplot[0], 0.05), ':', color=mycolor)
    confidence_interval = [st.t.interval(confidence=0.99, df=len(i) - 1, loc=np.mean(i), scale=st.sem(i)) for i in toplot[0]]
    ax.fill_between(unique_variable_parameters, [i[1] for i in confidence_interval],
                    [i[0] for i in confidence_interval],
                    color=mycolor, alpha=0.5)


plot_LBT_wait_times(dataset, colors[0], "Delay", ax)
ax2 = ax.twinx()
plot_LBT_retries(dataset, colors[3], "Retransmission attempts", ax2)
# ax.set_xticks(np.arange(len(unique_base_scenarios)), labels=unique_base_scenarios)
# ax.set_yticks(np.arange(len(unique_variable_parameters)), labels=unique_variable_parameters)
ax.grid(which='major', alpha=0.2)
leg = fig.legend(loc="upper left",
           bbox_to_anchor=(0.19, 0.89))  # , handleheight=0.9, labelspacing=0.2, handlelength=0.7,fontsize=13)#,
for line in leg.get_lines():
    line.set_linewidth(4.0)
plt.gcf().subplots_adjust(bottom=0.19)
plt.gcf().subplots_adjust(left=0.18)
plt.gcf().subplots_adjust(right=0.85)
plt.gcf().subplots_adjust(top=0.9)
ax.set_xlabel('Listen time [ms]')
ax.set_ylabel('Delay [ms]')
ax2.set_ylabel('Retransmission attempts')
# plt.show()
plt.savefig(out_LBT)
plt.close()

plt.rcParams.update({'font.size': 26})
plt.rcParams['figure.figsize'] = [10, 6]
fig, ax = plt.subplots()
plot_run(dataset, colors[0], "")
plt.ylim([4, 6])
# ax.set_xticks(np.arange(len(unique_base_scenarios)), labels=unique_base_scenarios)
# ax.set_yticks(np.arange(len(unique_variable_parameters)), labels=unique_variable_parameters)
ax.grid(which='major', alpha=0.2)
# plt.legend(loc="lower right", ncol=2, bbox_to_anchor=(1.1, 1),
#           fontsize=13)  # , handleheight=0.9, labelspacing=0.2, handlelength=0.7,fontsize=13)#,
plt.gcf().subplots_adjust(bottom=0.19)
plt.gcf().subplots_adjust(left=0.18)
plt.gcf().subplots_adjust(top=0.9)
plt.xlabel('Listen time [ms]')
plt.ylabel('Collision probability [%]')
# plt.show()
plt.savefig(out_Collision_prob)
plt.close()
