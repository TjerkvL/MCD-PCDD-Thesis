import pandas as pd
import csv
from src import configurations as config
from src.data_classes.class_input import InputParameters
import datetime
import ast
import os
import random
import numpy as np
import itertools
from generate_collection_of_logs import *





data = {
    "Process_tree_complexity": "",
    "Process_tree_evolution_proportion": "",
    "Number_event_logs": "",
    "Number_traces_per_process_model_version": "",
    "Number_traces_for_gradual_change": "",
    "Change_type": "",
    "Drift_types": "",
    "Number_drifts_per_log": "",
    "Noise": "",
    "Noisy_trace_prob": "",
    "Noisy_event_prob": "",
    "Trace_exp_arrival_sec": "",
    "Task_exp_duration_sec": "",
    "Gradual_drift_type": "",
    "Incremental_drift_number": "",
    "Recurring_drift_number": ""
}

def generate_random_values(min_value, max_value):
    first_value = random.uniform(min_value, max_value)
    second_value = random.uniform(first_value, max_value)
    return (round(first_value,1), round(second_value,1))

def link_values(rand_val:tuple):
    return str(rand_val[0]) +"-"+str(rand_val[1])

def transform_tup_val_to_int(rand_val:tuple):
    rand_val_int = (int(rand_val[0]),int(rand_val[1]))
    return rand_val_int

def link_values_int(rand_val:tuple):
    return link_values(transform_tup_val_to_int(rand_val))


def generate_combinations():
    words = ["sudden", "gradual", "incremental", "recurring"]
    combinations = []

    # Generate combinations of different lengths
    for r in range(1, len(words) + 1):
        combos = itertools.combinations(words, r)
        for combo in combos:
            combinations.append(", ".join(combo))

    return combinations

def fill_param_file():
    for key in data.keys():
        if key == "Process_tree_complexity":
            data[key] = random.choice(["simple","complex"])
        elif key == "Process_tree_evolution_proportion":
            data[key] = random.choice([link_values(generate_random_values(0,1)),round(random.uniform(0,1),1)])
        elif key == "Number_event_logs":
            data[key] = random.randint(1, 100)
        elif key == "Number_traces_per_process_model_version":
            data[key] = random.choice([link_values_int(generate_random_values(1000,3000)),int(random.uniform(1000,3000))])
        elif key == "Number_traces_for_gradual_change":
            data[key] = random.choice([link_values_int(generate_random_values(100,500)),int(random.uniform(100,500))])
        elif key == "Change_type":
            data[key] = random.choice(["sudden","gradual","sudden, gradual"])
        elif key == "Drift_types":
            data[key] = random.choice(generate_combinations())
        elif key == "Number_drifts_per_log":
            data[key] = random.choice([link_values_int(generate_random_values(1,15)),int(random.uniform(1,15))])
        elif key == "Noise":
            data[key] = random.choice([True,False])
        elif key ==  "Noisy_trace_prob":
            data[key] = random.choice([link_values(generate_random_values(0,1)),round(random.uniform(0,1),1)])
        elif key ==  "Noisy_event_prob":
            data[key] = random.choice([link_values(generate_random_values(0,1)),round(random.uniform(0,1),1)])
        elif key == "Trace_exp_arrival_sec":
            data[key] = int(random.uniform(10000,60000))

        elif key == "Task_exp_duration_sec":
            data[key] = int(random.uniform(100000,600000))
        elif key == "Gradual_drift_type":
            data[key] = random.choice(["linear","exponential","linear, exponential"])
        elif key == "Incremental_drift_number":
            data[key] = random.choice([link_values_int(generate_random_values(1,7)),int(random.uniform(1,7))])
        elif key == "Recurring_drift_number":
            data[key] = random.choice([link_values_int(generate_random_values(1,7)),int(random.uniform(1,7))])

    with open("param_empty", "w") as file:
        for key, value in data.items():
            file.write(key + ": " + str(value) + "\n")

