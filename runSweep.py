from joblib import Parallel, delayed
import sys
import os

# Import off-path folders
currentPath = os.getcwd()

sys.path.append(currentPath + '/src/')
sys.path.append(currentPath + '/src/caches/') 
print(currentPath + '/src/cache-analysis/caches/')

import numpy as np
import json
import os
import matplotlib.pyplot as plt
from cacheObj import cacheObj
from leakageCalculator import *
from tqdm import tqdm
import itertools
from batch_primeProbe import main as primeprobe

# ========== Experiment Parameters ==========

# The number of attacker priming steps
primingStepRange = [1,2,4,8]
# The number of lines the attacker will prime/probe
primingRatioRange = np.arange(0,2048,16)
# The number of accesses the *victim* will perform
numAccRangeRange = [np.arange(15,28)]
# The number of cache hash groups (only valid for skewed caches)
numHGRange = [1]

# ===========================================

# For a single experiment:
def singleSub(primingSteps, primingRatio, numAccRange, numHG):
    x2y = dict()
    y_set = set()

    for numAcc in numAccRange:
        victDict = {}
        for i in range(numAcc):
            victDict[i] = i * 64 + 100000000

        cache = cacheObj(None, victDict)
        cache.subSectionLines = primingRatio
        cache.numPrime = primingSteps
        cache.iterations = 5000
        cache.cacheType = 0
        cache.numHG = numHG

        y, x = primeprobe(cache.info())
        
        if x not in x2y.keys():
            x2y[x] = []

        x2y[x] = x2y[x] + y
        y_set = y_set.union(set(y))

        leakage = calculateLeakage(x2y, False)

    return leakage

# Construct list of possible experiments
experiments = []
for primes in primingStepRange:
    for ratio in primingRatioRange:
        for numAccRange in numAccRangeRange:
            for numHG in numHGRange:
                experiments.append((primes, ratio, numAccRange, numHG))

# Excute these experiments in parallel (using all CPUs)
leakage_arr = []
leakage_arr = Parallel(n_jobs=-1)(delayed(singleSub)(primes, ratio, numAccRange, numHG) for (primes, ratio, numAccRange, numHG) in tqdm(experiments))

df = pd.DataFrame(list(experiments), columns=["NumPrimes", "Ratio", "NumAcc", "numHG"])
df['Leakage'] = leakage_arr

df.to_pickle(currentPath + "/results.pkl")
print("Done!")


