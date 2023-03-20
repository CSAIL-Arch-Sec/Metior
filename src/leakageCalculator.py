import math
from matplotlib.pyplot import ylabel
import pandas as pd
import matplotlib.pyplot as plt


def calculateLeakage(x2y, plot=True, divisor=1):

    if divisor != 1:
        for x in x2y.keys():
            #print(x2y[x])
            x_list = x2y[x]
            divided_list = []

            for i in x_list:
                divided_list.append(tuple([a//divisor for a in i]))

            x2y[x] = divided_list

    y_set = set()

    pandas_index = []
    pandas_y = []
    pandas_dict = dict()

    # Discover all possible y values
    for x in x2y.keys():
        for y in x2y[x]:
            y_set.add(y)

    prob_summation = 0
    for y in sorted(y_set):
        pandas_index.append(y)
        local_y = []

        max_prob = 0
        
        # Iterate through all x
        for x in x2y.keys():
            if x not in pandas_dict.keys():
                pandas_dict[x] = []
            prob = x2y[x].count(y) / len(x2y[x])
            pandas_dict[x].append(prob)
            if prob > max_prob:
                max_prob = prob

        assert(max_prob != 0)

        prob_summation += max_prob

    if plot:
        df = pd.DataFrame(dict(sorted(pandas_dict.items())), index=pandas_index).plot.bar(figsize=(20, 10), xlabel="Shaped Inter-Arrival Pattern", label="Number of Distinct Cache Accesses")
        plt.show()

    return math.log2(prob_summation)
