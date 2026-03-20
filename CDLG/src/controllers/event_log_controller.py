import datetime
import itertools
from random import randint
import numpy
from pm4py.objects.log.obj import EventLog
from copy import deepcopy



def combine_two_logs(log_1, log_2):
    """ Merging of two event logs

    :param log_one: first event log
    :param log_two: second event log
    :return: combined event log
    """
    log_one = deepcopy(log_1)
    log_two = deepcopy(log_2)
    # join two logs and add trace belonging to a process version
    log_combined = EventLog()
    last_model_version = 0
    for trace in log_one:
        try:
            last_model_version = trace.attributes['model:version']
        except:
            trace.attributes['model:version'] = last_model_version
        log_combined.append(trace)

    for trace in log_two:
        trace.attributes['model:version'] = last_model_version + 1
        log_combined.append(trace)

    # Update trace ids to be unique
    trace_id = 0
    for trace in log_combined:
        trace.attributes['concept:name'] = str(trace_id)
        trace_id += 1

    return log_combined


def generate_two_parts_of_event_log(log, nu_trace):
    """ Generating two event logs from one

    :param log: event log
    :param nu_trace: number of trace, by which the event log should be divided
    :return: the two separate event logs
    """
    i = 0
    log_one = EventLog()
    log_two = EventLog()
    for trace in log:
        if i < nu_trace:
            i = i + 1
            log_one.append(trace)
        else:
            log_two.append(trace)
    return log_one, log_two


def generate_several_parts_of_event_log(log, number):
    """ Generating several event logs from one

    :param log: event log
    :param number: number of generated event logs
    :return: list of event logs
    """
    nu_traces_first_log = length_of_log(log)
    nu_traces_per_log = int(round(nu_traces_first_log / number + 0.0001))
    logs = []
    count = 1
    log_two = log
    while count < number:
        log_one, log_two = generate_two_parts_of_event_log(log_two, nu_traces_per_log)
        logs.append(log_one)
        count = count + 1
    logs.append(log_two)
    return logs


def add_duration_to_log_old(log, datestamp, min_duration, max_duration):
    """ Adding duration to the activities in the event log

    :param max_duration: minimum for the duration of one activity in seconds
    :param min_duration: maximum for the duration of one activity in seconds
    :param datestamp: starting time of the first trace
    :param log: event log
    :return: realistic event log
    """
    duration = {}
    time_first = datestamp
    for trace in log:
        if trace.__len__() != 0:
            z = trace.__getitem__(0)
            z['time:timestamp'] = time_first
            break
    first_of_first = True
    duration_last_trace = 0
    for trace in log:
        j = 1
        time = 0
        if trace.__len__() != 0:
            if first_of_first:
                first_of_first = False
                first = trace.__getitem__(0)
            else:
                first = trace.__getitem__(0)
                if duration_last_trace > min_duration:
                    time_one = randint(min_duration, duration_last_trace)
                else:
                    time_one = randint(duration_last_trace, min_duration)
                first['time:timestamp'] = time_first + datetime.timedelta(0, time_one)
                time_first = first['time:timestamp']
            if first['concept:name'] in duration.keys():
                first['duration:seconds'] = int(numpy.random.exponential(duration[first['concept:name']]))
                time = duration[first['concept:name']]
            else:
                i = randint(min_duration, max_duration)
                duration[first['concept:name']] = i
                first['duration:seconds'] = i
                time = i
        while j < trace.__len__():
            a = trace.__getitem__(j)
            if a['concept:name'] in duration.keys():
                a['duration:seconds'] = int(numpy.random.exponential(duration[a['concept:name']]))
                a['time:timestamp'] = time_first + datetime.timedelta(0, time)
                time = time + duration[a['concept:name']]
            else:
                i = randint(min_duration, max_duration)
                duration[a['concept:name']] = i
                a['duration:seconds'] = i
                a['time:timestamp'] = time_first + datetime.timedelta(0, time)
                time = time + i
            j = j + 1
        if trace.__len__() != 0:
            tr_first = trace.__getitem__(0)
            tr_last = trace.__getitem__(trace.__len__()-1)
            dur = tr_last['time:timestamp'] - tr_first['time:timestamp']
            duration_last_trace = int(dur.total_seconds() + tr_last['duration:seconds'])
    count = 0
    for trace in log:
        trace._set_attributes({'concept:name': str(count)})
        count = 1 + count


def get_timestamp_log(log, nu_traces, part):
    """ Getting the timestamp of a specific trace

    :param log: event log
    :param nu_traces: Amount of traces in the event log
    :param part: place of trace as a proportion of the total traces
    :return: timestamp of specific trace
    """
    if part == 0:
        nu_trace = 0
    elif part == 1:
        nu_trace = nu_traces - 1
    else:
        nu_trace = int(round(nu_traces * part + 0.0001))
    trace = log[nu_trace]
    if trace.__len__() == 0:
        return "empty trace"
    else:
        return trace.__getitem__(0)['time:timestamp']


def get_num_trace(traces, part):
    if part == 0:
        num_trace = 0
    elif part == 1:
        num_trace = traces
    else:
        num_trace = int(round(traces * part + 0.0001))
    return num_trace


def replace_traces_of_log(main_log, log_two, start_point):
    """ Replacing traces with new traces

    :param main_log: resulting event log
    :param log_two: event log with new traces
    :param start_point: starting point of traces replacement
    :return: event log
    """
    result_log = EventLog()
    start = int(round(length_of_log(main_log) * start_point + 0.0001))
    j = 0
    for trace in main_log:
        if j < start:
            result_log.append(trace)
            j = j + 1
        else:
            break
    for trace in log_two:
        result_log.append(trace)
        j = j + 1
    i = 0
    for trace in main_log:
        if i == j:
            result_log.append(trace)
            i = i + 1
            j = j + 1
        else:
            i = i + 1
    return result_log


def get_part_of_log(log, proportion):
    """ Getting part of a event log

    :param log: event log
    :param proportion: proportion of total traces where the part starts
    :return: event log
    """
    result = EventLog()
    end = int(round(length_of_log(log) * proportion + 0.0001))
    i = 0
    for trace in log:
        if i < end:
            result.append(trace)
            i = i + 1
        else:
            break
    return result


def include_noise_in_log(log_total, log_noise, start_noise, end_noise):
    """ Introduction of noise in an event log

    :param log_total: event log
    :param log_noise: event log containing all noise traces
    :param start_noise: Starting point of noise
    :param end_noise: Ending point of noise
    :return: event log with noise
    """
    log_result_with_noise = EventLog()
    start = int(round((length_of_log(log_total) * start_noise) + 0.0001))
    stop = int(round((length_of_log(log_total) * end_noise) + 0.0001))
    amount_noise = length_of_log(log_noise)
    amount_not_noise = int(round(
        ((length_of_log(log_total) * end_noise) - (length_of_log(log_total) * start_noise) - amount_noise) + 0.0001))
    i = 0
    a = 0
    log_result_with_noise = EventLog(itertools.chain(log_result_with_noise, log_total[:start]))
    j = start
    norm = int(round((amount_not_noise / amount_noise) + 0.0001))
    rest = norm - (amount_not_noise / amount_noise)
    if rest <= 0:
        rest_adding = int(round((rest * amount_noise*(-1))+0.0001))
        while j < stop:
            norm_start = randint(0, norm)
            norm_end = norm - norm_start
            add = randint(0, 1)
            if a < rest_adding and add == 1:
                log_result_with_noise = EventLog(itertools.chain(log_result_with_noise, log_total[j:j+norm_start+1]))
                j = j + norm_start + 1
                a = a + 1
            else:
                log_result_with_noise = EventLog(itertools.chain(log_result_with_noise, log_total[j:j+norm_start]))
                j = j + norm_start
            k = 0
            for trace in log_noise:
                if k == i:
                    log_result_with_noise.append(trace)
                    j = j + 1
                    i = i + 1
                    break
                else:
                    k = k + 1
            m = 0
            n = 0
            for trace in log_total:
                if m < norm_end and n == j and j < stop:
                    log_result_with_noise.append(trace)
                    j = j + 1
                    n = n + 1
                    m = m + 1
                elif n == j and j < stop and a < rest_adding and add == 0:
                    log_result_with_noise.append(trace)
                    a = a + 1
                    j = j + 1
                    n = n + 1
                elif n > j:
                    break
                else:
                    n = n + 1
    else:
        rest_adding = int(round(amount_noise - (amount_not_noise/norm)+0.0001))
        while j < stop:
            norm_start = randint(0, norm)
            norm_end = norm - norm_start
            m = 0
            n = 0
            for trace in log_total:
                if m < norm_start and n == j and j < (stop - 1):
                    log_result_with_noise.append(trace)
                    j = j + 1
                    n = n + 1
                    m = m + 1
                elif n > j:
                    break
                else:
                    n = n + 1
            k = 0
            for trace in log_noise:
                if k == i:
                    log_result_with_noise.append(trace)
                    j = j + 1
                    i = i + 1
                    break
                else:
                    k = k + 1
            m = 0
            n = 0
            for trace in log_total:
                if m < norm_end and n == j and j < stop:
                    log_result_with_noise.append(trace)
                    j = j + 1
                    n = n + 1
                    m = m + 1
                elif n > j:
                    break
                else:
                    n = n + 1
            k = 0
            for trace in log_noise:
                if k == i and a < rest_adding:
                    log_result_with_noise.append(trace)
                    j = j + 1
                    i = i + 1
                    a = a + 1
                    break
                else:
                    k = k + 1
    count = 0
    log_result_with_noise = EventLog(itertools.chain(log_result_with_noise, log_total[stop:]))
    for trace in log_result_with_noise:
        trace._set_attributes({'concept:name': str(count)})
        count = 1 + count
    return log_result_with_noise


def length_of_log(log):
    return len(log)
