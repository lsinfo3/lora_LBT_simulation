import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as st
import json

plt.rcParams.update({'font.size': 24})
plt.rcParams['figure.figsize'] = [20, 6]
fig, ax = plt.subplots(2, sharex=True)
colors = plt.cm.copper(np.linspace(0, 1, 5))

with open("collision_probability.json") as jsonfile:
    data = json.load(jsonfile)
names = data["placement_base_scenario"]
names = [str(x).split('_')[1] for x in names]
print(names)
retries = data["LBT_retries"]
for x in range(len(retries)):
    for y in range(len(retries[x])):
        retries[x][y] = retries[x][y][0]

delay = data["LBT_total_wait_time"]
for x in range(len(delay)):
    for y in range(len(delay[x])):
        delay[x][y] = delay[x][y][0]

with open("collision_probability_RW.json") as jsonfile:
    data = json.load(jsonfile)
names = data["placement_base_scenario"]
names = [str(x).split('_')[1] for x in names]
print(names)
retries_RW = data["LBT_retries"]
for x in range(len(retries_RW)):
    for y in range(len(retries_RW[x])):
        retries_RW[x][y] = retries_RW[x][y][0]

delay_RW = data["LBT_total_wait_time"]
for x in range(len(delay_RW)):
    for y in range(len(delay_RW[x])):
        delay_RW[x][y] = delay_RW[x][y][0]
print([np.mean(x) for x in retries])
print([np.mean(x) for x in delay])
x = 0
for curr in names:
    ax[0].bar(x, np.mean(retries[names.index(curr)]), width=0.8,color=colors[1])
    confidence_interval = st.t.interval(confidence=0.99, df=len(retries[names.index(curr)]) - 1,
                                        loc=np.mean(retries[names.index(curr)]),
                                        scale=st.sem(retries[names.index(curr)]))
    ax[0].errorbar([x], [np.mean(retries[names.index(curr)])],
                 yerr=[[np.mean(retries[names.index(curr)])-confidence_interval[0]],[confidence_interval[1] - np.mean(retries[names.index(curr)])]], ecolor="black",capsize=10)
    x += 1
    ax[0].bar(x, np.mean(retries_RW[names.index(curr)]), width=0.8,color=colors[3])
    confidence_interval = st.t.interval(confidence=0.99, df=len(retries_RW[names.index(curr)]) - 1,
                                        loc=np.mean(retries_RW[names.index(curr)]),
                                        scale=st.sem(retries_RW[names.index(curr)]))
    ax[0].errorbar([x], [np.mean(retries_RW[names.index(curr)])],
                   yerr=[[np.mean(retries_RW[names.index(curr)]) - confidence_interval[0]],
                         [confidence_interval[1] - np.mean(retries_RW[names.index(curr)])]], ecolor="black", capsize=10)
    x+=1
    print(np.mean(retries_RW[names.index(curr)]) / np.mean(retries[names.index(curr)]))

x = 0
print()
for curr in names:
    ax[1].bar(x, np.mean(delay[names.index(curr)]), width=0.8,color=colors[1])
    confidence_interval = st.t.interval(confidence=0.99, df=len(delay[names.index(curr)]) - 1,
                                        loc=np.mean(delay[names.index(curr)]),
                                        scale=st.sem(delay[names.index(curr)]))
    ax[1].errorbar([x], [np.mean(delay[names.index(curr)])],
                 yerr=[[np.mean(delay[names.index(curr)])-confidence_interval[0]],[confidence_interval[1] - np.mean(delay[names.index(curr)])]], ecolor="black",capsize=10)
    x += 1
    ax[1].bar(x, np.mean(delay_RW[names.index(curr)]), width=0.8,color=colors[3])
    confidence_interval = st.t.interval(confidence=0.99, df=len(delay_RW[names.index(curr)]) - 1,
                                        loc=np.mean(delay_RW[names.index(curr)]),
                                        scale=st.sem(delay_RW[names.index(curr)]))
    ax[1].errorbar([x], [np.mean(delay_RW[names.index(curr)])],
                   yerr=[[np.mean(delay_RW[names.index(curr)]) - confidence_interval[0]],
                         [confidence_interval[1] - np.mean(delay_RW[names.index(curr)])]], ecolor="black", capsize=10)
    x+=1
    print(np.mean(delay_RW[names.index(curr)]) / np.mean(delay[names.index(curr)]))

#plt.xlabel('X-Label')
#plt.ylabel('Y-Label')
ax[0].tick_params(bottom = False)
ax[0].set_ylabel("Retrans. att.")
ax[1].set_ylabel("Delay [ms]")
max_retries=max(max(retries))
max_retries_RW=max(max(retries_RW))
max_retries = max(max_retries_RW,max_retries)
max_delay=max(max(delay))
max_delay_RW=max(max(delay_RW))
max_delay = max(max_delay_RW,max_delay)
ax[0].set_yticks(np.arange(0,max_retries,0.01))
ax[1].set_yticks(np.arange(0,max_delay,5))
Ticklabels = ["SYD","SYD (RW)","SF","SF (RW)", "LON", "LON (RW)", "BK", "BK (RW)", "NYC", "NYC (RW)", "SH", "SH (RW)", "WÜ", "WÜ (RW)","M","M (RW)"]
ax[0].set_xticks(np.arange(0,16, 1))
ax[0].set_xticklabels(Ticklabels)
# plt.xscale('log')
plt.gcf().subplots_adjust(top=0.9)
plt.gcf().subplots_adjust(left=0.065)
plt.gcf().subplots_adjust(right=0.95)
plt.grid(which='major')
# plt.legend(loc="lower right",ncol=2,bbox_to_anchor=(1.1,1),fontsize=13)#, handleheight=0.9, labelspacing=0.2, handlelength=0.7,fontsize=13)#,
plt.gcf().subplots_adjust(bottom=0.25)

# ax.set_xticks(np.arange(0,1000, 100))
plt.xticks(rotation=50,horizontalalignment='right')
ax[0].grid(which='major', alpha=0.2)
ax[1].grid(which='major', alpha=0.2)
# plt.show()
plt.savefig('S5.pdf')
plt.close()
