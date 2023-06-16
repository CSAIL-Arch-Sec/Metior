# Metior

This is the official demonstration code for Metior, a comprehensive model to evaluate obfuscating side-channel defense schemes.

This repository contains the code required to reproduce Figure 7 of Case Study I.
Specifically, it contains code that:

1. Models varying secure cache architectures under different configurations.
2. Performs Monte Carlo simulations using these models to derive the probabilistic observations under a cache-occupancy attack scenario.
3. Derives the Maximal Leakage for each attack strategy considered, plotting the space sweep using matplotlib.

## Setup

Due to the large number of experiments required, we suggest running this demonstration on a many-core (48+) server.

After cloning this repository, install the requisite Python 3 dependencies by running *pip3 install -r requirements.txt*.

## Replicating Figure 7

To replicate Figure 7, first run *python3 runSweep.py*, which will use all cores on the machine to run the Monte-Carlo simulation. 
This will write the results to *results.pkl*, which can be then plotted by running *python3 plotResults.py results.pkl*.

## Code Organization

A brief overview of the source code included in this repository (found in *src/*) is as follows:

- *primeProbe.py*: Implements the routines required for the attacker to prime and probe the victim cache during a cache occupancy attack.
- *batch_primeProbe.py*: Organizes arguments, then calls the Prime+Probe cache occupancy attack routines.
- *cacheObj.py*: Defines default parameters for the cache architecture being studied (including number of cache lines, line size, etc.).
- *dag.py/dagGen.py*: Internal DAG representations for the attacker/victim's access patterns.
- *calculateLeakage.py**: Computes the Maximal Leakage for an attacker's observations. The input is a dictionary, where the keys are the victim modulation pattern, and the values are lists of attacker observations.
- *caches/*: Includes models for varying secure cache architectures.
