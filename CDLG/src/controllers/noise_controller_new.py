from copy import deepcopy
import random
from pm4py.objects.log.obj import EventLog, Trace, Event
import numpy as np
import datetime


def insert_noise(log: EventLog, noisy_trace_prob, noisy_event_prob, task_exp_duration_sec):
    classes = _get_event_classes(log)
    log_new = EventLog()
    for trace in log:
        if len(trace) > 0:
            trace_cpy = deepcopy(trace)
            # check if trace makes random selection
            if random.random() <= noisy_trace_prob:
                insert_more_noise = True
                while insert_more_noise:
                    # randomly select which kind of noise to insert
                    noise_type = random.randint(0, 2)
                    if noise_type == 0:
                        trace_cpy = _insert_event(trace_cpy, classes, task_exp_duration_sec)
                    if noise_type == 1:
                        # Note: do not remove events if a trace has only one activity
                        if len(trace_cpy) > 1:
                            trace_cpy = _remove_event(trace_cpy)
                        else:
                            trace_cpy = _insert_event(trace_cpy, classes, task_exp_duration_sec)
                    if noise_type == 2:
                        # Note: swapping only possible if at least 2 events are present
                        if len(trace_cpy) > 1:
                            trace_cpy = _swap_events(trace_cpy)
                        else:
                            trace_cpy = _insert_event(trace_cpy, classes, task_exp_duration_sec)

                    # flip coin to see if more noise will be inserted
                    insert_more_noise = (random.random() <= noisy_event_prob)
            log_new.append(trace_cpy)
    return log_new


def _remove_event(trace: Trace):
    if len(trace) == 1:
        return trace

    # create a new trace that stores the new order of events
    trace2 = Trace()
    trace2._set_attributes(trace.attributes)

    del_index = random.randint(0, len(trace) - 1)
    for i in range(0, len(trace)):
        if i != del_index:
            trace2.append(trace[i])

    return trace2


def _insert_event(trace: Trace, tasks, task_exp_duration_sec):
    # get all timestamps of initial events
    all_timestamps = [e["time:timestamp"] for e in trace]

    # Create a new timestamp and append it to all timestamps
    task_duration_sec = int(np.random.exponential(task_exp_duration_sec))
    new_timestamp = max(all_timestamps) + datetime.timedelta(seconds=task_duration_sec)
    all_timestamps.append(new_timestamp)
    all_timestamps.sort()

    # insert a new event to a trace
    # get event index, activity label
    ins_index = random.randint(0, len(trace))
    task = random.choice(list(tasks))

    # create and insert a new event wit a given task label into a trace
    e = Event()
    e["concept:name"] = task
    trace.insert(ins_index, e)
    # reassign events' timestamps
    for i, e in enumerate(trace):
        e["time:timestamp"] = all_timestamps[i]
    return trace


def _swap_events(trace: Trace):
    # events swapping can be done if there are at least two events in a trace
    if len(trace) == 1:
        return trace

    # create a new trace that stores the new order of events
    trace2 = Trace()
    trace2._set_attributes(trace.attributes)

    # select two event indices to be swapped
    indices = list(range(len(trace)))
    index1 = random.choice(indices)
    indices.remove(index1)
    index2 = random.choice(indices)

    # save the initial timestamps of events to be swapped
    timestamp_index_1 = deepcopy(trace[index1]["time:timestamp"])
    timestamp_index_2 = deepcopy(trace[index2]["time:timestamp"])
    # main iteration
    for i in range(len(trace)):
        if i == index1 or i == index2:
            if i == index1:
                trace[index2]["time:timestamp"] = timestamp_index_1
                trace2.append(trace[index2])
            else:
                trace[index1]["time:timestamp"] = timestamp_index_2
                trace2.append(trace[index1])
        else:
            trace2.append(trace[i])
    return trace2


def _get_event_classes(log):
    classes = set()
    for trace in log:
        for event in trace:
            classes.add(event["concept:name"])
    return classes
