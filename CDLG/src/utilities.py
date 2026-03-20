import datetime
import os
import random
import time
from random import uniform, randint
from datetime import timedelta, datetime
import numpy
from pm4py.util.xes_constants import DEFAULT_TRANSITION_KEY
import re
from src import configurations as config
from src.controllers.process_tree_controller import generate_specific_trees, generate_tree_from_file
from src.data_classes.class_axillary import TraceAttributes
from src.data_classes.class_input import get_parameters
from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.objects.process_tree import semantics


def remove_empty_trace(log):
    new_log = EventLog()
    for trace in log:
        if len(trace) != 0:
            new_log.append(trace)
    return new_log


def generate_first_event_log_part_from_initial_process_tree(tree_initial, par, drift_n):
    # Note:
    # If not rescaling the log size in the case when no drifts are present,
    # then logs without drift tend to be smaller than those with drifts.
    # This is due to the fact that logs with drift combine several process version,
    # when iterating through all drift_ids (below). By randomly selecting a scale below,
    # we ensure that logs without drift can have size of one or more process version as well.
    num_traces = select_random(par.Number_traces_per_process_model_version, option='uniform_int')

    if drift_n == 0:
        scale = select_random(par.Number_drifts_per_log, option='uniform_int') + 1
        event_log = generate_log_from_tree(tree_initial, scale * num_traces)
    else:
        event_log = generate_log_from_tree(tree_initial, num_traces)

    return event_log


def generate_log_from_tree(tree, num_traces):

    event_log = semantics.generate_log(tree, num_traces)
    event_log = remove_empty_trace(event_log)
    return event_log


def select_random(data: list, option: str = 'random') -> any:
    if len(data) == 1:
        data_selected = data[0]
    elif len(data) == 2 and option == 'uniform':
        data_selected = uniform(data[0], data[1])
    elif len(data) == 2 and option == 'uniform_int':
        data_selected = randint(data[0], data[1])
    elif len(data) == 2 and option == 'uniform_step':
        data_selected = round(uniform(data[0], data[1]), 1)
    elif option == 'random':
        data_selected = random.choice(data)
    else:
        data_selected = None
        Warning(f"Check function 'select_random' call: {data, option, data_selected}")

    if isinstance(data, float):
        data_selected = round(data_selected, 2)

    return data_selected


def add_duration_to_log(log, par=None):

    assert len(log) > 0, "Log has no trace!"
    assert len(log) > 2, "Log has less than 2 trace!"

    if par is None:
        par = get_parameters(config.PARAMETER_NAME)

    log_start_timestamp_list = [datetime.strptime(v, '%Y/%m/%d %H:%M:%S') for v in config.FIRST_TIMESTAMP.split(',')]
    log_start_timestamp = select_random(log_start_timestamp_list, option='random')
    trace_exp_arrival_sec = select_random(par.Trace_exp_arrival_sec, option='uniform_int')
    task_exp_duration_sec = select_random(par.Task_exp_duration_sec, option='uniform_int')

    # Main loop over all traces and events
    for index_trace, trace in enumerate(log):
        assert len(trace) > 0, "Trace has no events"
        if index_trace == 0:
            # First trace
            for index_event, event in enumerate(trace):
                if index_event == 0:
                    # Define the timestamp of the first trace and first event
                    log[index_trace][index_event][TraceAttributes.timestamp.value] = log_start_timestamp
                else:
                    # Define the timestamp of all other events in the first
                    task_duration = numpy.random.exponential(task_exp_duration_sec)
                    value = trace[index_event - 1][TraceAttributes.timestamp.value]
                    event[TraceAttributes.timestamp.value] = value + timedelta(seconds=task_duration)
        else:
            # All other traces
            for index_event, event in enumerate(trace):
                if index_event == 0:
                    # The timestamp of the first event depends on the start timestamp of the previous trace + exp. timedelta
                    trace_arrival = numpy.random.exponential(trace_exp_arrival_sec)
                    value = log[index_trace - 1][index_event][TraceAttributes.timestamp.value]
                    event[TraceAttributes.timestamp.value] = value + timedelta(seconds=trace_arrival)
                else:
                    # The timestamp of the next event depends on the previous timestamp + exp. timedelta
                    task_duration = numpy.random.exponential(task_exp_duration_sec)
                    value = trace[index_event - 1][TraceAttributes.timestamp.value]
                    event[TraceAttributes.timestamp.value] = value + timedelta(seconds=task_duration)
                    # print(f"Event log length: {len(log)}")
                    # print(log)
                    # print(f"Trace: {trace}, trace length: {len(trace)}")
                    # print(f"Index: {index_event}, and event: {event}")
                    # ValueError("Error")

    add_event_lifecycle(log)

    return None


def add_event_lifecycle(log):
    for trace in log:
        for event in trace:
            event[DEFAULT_TRANSITION_KEY] = 'complete'
    return None


def add_unique_trace_ids(log):
    trace_id = 1
    for trace in log:
        trace.attributes[TraceAttributes.concept_name.value] = str(trace_id)
        trace_id += 1
    return None


def extract_list_from_string(string_of_list: str):
    return [int(int_val_str) for int_val_str in re.findall(r'\d+', string_of_list)]


def remove_duplicates(strings:list):
    seen = set()
    result = []
    for string in strings:
        if string not in seen:
            seen.add(string)
            result.append(string)
    return result

class Log_attr_params():
    drift_info = "drift:info"
    children = "children"
    change_info = "change_info"
    change_type = "change_type"
    process_tree_before = "process_tree_before"
    process_tree_after = "process_tree_after"
    activities_deleted = "activities_deleted"
    activities_added = "activities_added"
    activities_moved = "activities_moved"
    drift_type = "drift_type"
    process_perspective = "process_perspective"
    change_trace_index = "change_trace_index"


def generate_initial_tree(complexity_options_list: list, file_path_to_own_models: str) -> dict:
    """
    TODO: write what this function does
    :param complexity_options_list:
    :param file_path_to_own_models:
    :return:
    """
    complexity = select_random(complexity_options_list, option='random')
    if file_path_to_own_models is None:
        generated_process_tree = generate_specific_trees(complexity)
    else:
        generated_process_tree = generate_tree_from_file(file_path_to_own_models)
    return generated_process_tree


def creat_output_folder(path: str = config.DEFAULT_OUTPUT_DIR, folder_name: str = config.PARAMETER_NAME):
    out_folder = os.path.join(path, folder_name + '_' + str(int(time.time())))
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)
    return out_folder


