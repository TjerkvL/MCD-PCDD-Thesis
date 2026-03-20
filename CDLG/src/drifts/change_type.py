from src.utilities import select_random
from src.data_classes.class_axillary import ChangeTypes, TraceAttributes
from src.utilities import generate_log_from_tree
import math
import numpy
from pm4py.objects.log.obj import EventLog
from random import randint
from copy import deepcopy
from src.controllers.process_tree_controller import randomize_tree_one, randomize_tree_two,\
    randomize_tree_three, randomize_tree_more, count_real_acs
import src.configurations as config


def combine_two_logs_with_certain_change_type(event_log, drift_instance, par, axillary: list = []):

    if axillary:
        tree_previous, tree_new, deleted_acs, added_acs, moved_acs = axillary
    else:
        # Get settings for the next process tree and change type
        tree_previous = drift_instance.get_previous_process_tree()
        ran_evolve = select_random(config.INCREMENTAL_EVOLUTION_SCOPE, option='uniform')
        tree_new, deleted_acs, added_acs, moved_acs = evolve_tree_randomly(tree_previous, ran_evolve)

    change_type = select_random(par.Change_type, option='random')
    if change_type == ChangeTypes.sudden.value:
        combined_log = combine_two_logs_sudden(event_log, tree_new, par)
        change_trace_index = [len(event_log) + 1]
    else:
        combined_log, help = combine_two_logs_gradual(event_log, tree_previous, tree_new, par)
        change_trace_index = [len(event_log) + 1, help]

    drift_instance.add_change_info(change_trace_index, change_type, tree_previous, tree_new, deleted_acs, added_acs, moved_acs)

    return combined_log, drift_instance


def extract_next_process_model_version(log):

    try:
        last_model_version_id = log[-1].attributes[TraceAttributes.model_version.value]
    except:
        last_model_version_id = 0

    next_process_model_version = last_model_version_id + 1
    return next_process_model_version


def add_process_model_version(log, model_version):

    for trace in log:
        trace.attributes[TraceAttributes.model_version.value] = model_version
    return log



def add_log2_to_log1(log_1, log_2):

    next_model_version_id = extract_next_process_model_version(log_1)
    if next_model_version_id == 1:
        log_1 = add_process_model_version(log_1, next_model_version_id)
        log_2 = add_process_model_version(log_2, next_model_version_id+1)
    else:
        log_2 = add_process_model_version(log_2, next_model_version_id)

    log_combined = deepcopy(log_1)
    log_two = deepcopy(log_2)
    for trace in log_two:
        log_combined.append(trace)
    return log_combined


def combine_two_logs_sudden(event_log, tree_new, parameters):
    """ Merging of two event logs

    :param log_one: first event log
    :param log_two: second event log
    :return: combined event log
    """

    num_traces = select_random(parameters.Number_traces_per_process_model_version, option='uniform_int')
    log_two = generate_log_from_tree(tree_new, num_traces)
    log_combined = add_log2_to_log1(event_log, log_two)

    return log_combined


def combine_two_logs_gradual(event_log, tree_previous, tree_new, parameters):

    # Generate transition phase
    num_traces_gradual_phase = select_random(parameters.Number_traces_for_gradual_change, option='uniform_int')
    gradual_type = select_random(parameters.Gradual_drift_type, option='random')
    log_transition = distribute_traces(tree_previous, tree_new, gradual_type, num_traces_gradual_phase)
    # Generate added log
    num_traces = select_random(parameters.Number_traces_per_process_model_version, option='uniform_int')
    log_two = generate_log_from_tree(tree_new, num_traces)
    # Combine initial log, transition, and log_two
    # TODO: do not assign a new trace id to traces during the transition phase
    log_with_transition = add_log2_to_log1(event_log, log_transition)
    log_extended = add_log2_to_log1(log_with_transition, log_two)

    return log_extended, len(log_with_transition)+1


def distribute_traces(tree_one, tree_two, distribute_type, nu_traces):
    """Linear or exponential distribution of the traces during the gradual drift

    :param tree_one: initial model
    :param tree_two: evolved model
    :param distribute_type: distribution type (linear, exponential)
    :param nu_traces: number of occurring traces during drift
    :return: An log only including the gradual drift part
    """
    result = EventLog()
    count = 0
    if distribute_type.strip() == 'linear':
        rest_one, rest_two, rounds, b = get_rest_parameter(nu_traces, distribute_type)
        x = 1
        most_one = rest_one + b * rounds
        most_two = rest_two + b * rounds
        while x <= rounds:
            if x == rounds:
                count = count + most_two
                log_t = generate_log_from_tree(tree_two, most_two)
            else:
                count = count + (x * b)
                log_t = generate_log_from_tree(tree_two, x * b)
            for t in log_t:
                result.append(t)
            if x == 1:
                count = count + most_one
                log_a = generate_log_from_tree(tree_one, most_one)
            else:
                count = count + ((rounds - (x - 1)) * b)
                log_a = generate_log_from_tree(tree_one, (rounds - (x - 1)) * b)
            for a in log_a:
                result.append(a)
            x = x + 1
    else:
        rest_one, rest_two, rounds, b = get_rest_parameter(nu_traces, distribute_type)
        x = 1
        most_one = rest_one + int(round(math.exp(rounds * b) + 0.0001))
        most_two = rest_two + int(round(math.exp(rounds * b) + 0.0001))
        while x <= rounds:
            if x == rounds:
                log_t = generate_log_from_tree(tree_two, most_two)
            else:
                log_t = generate_log_from_tree(tree_two, int(round(math.exp(x * b) + 0.0001)))
            for t in log_t:
                result.append(t)
            if x == 1:
                log_a = generate_log_from_tree(tree_one, most_one)
            else:
                log_a = generate_log_from_tree(tree_one, int(round(math.exp((rounds - (x - 1)) * b))))
            for a in log_a:
                result.append(a)
            x = x + 1
    return result



def get_rest_parameter(nu_traces, distribute_type):
    """ Calculation of the best parameters for the gradual drift.

    :param nu_traces: number of traces to be distributed
    :param distribute_type: mathematical type of distribution
    :return:
    """
    rests_one = []
    rests_two = []
    rounds = []
    nu_drift_model_one = int(round((nu_traces / 2) + 0.0001))
    nu_drift_model_two = nu_traces - nu_drift_model_one

    if distribute_type.strip() == 'exponential':
        b = 0.5
        while b <= 0.8:
            hel = 0
            rest_one = 1
            rest_two = 1
            round_l = 0
            while hel + int(round(math.exp((round_l + 1) * b) + 0.0001)) <= nu_drift_model_one:
                round_l = round_l + 1
                hel = hel + int(round(math.exp(round_l * b) + 0.0001))
                rest_one = nu_drift_model_one - hel
                rest_two = nu_drift_model_two - hel
            b = b + 0.1
            rests_one.append(rest_one)
            rests_two.append(rest_two)
            rounds.append(round_l)
    else:
        # linear distribution type
        b = 2
        while b < 6:
            hel = 0
            rest_one = 1
            rest_two = 1
            round_l = 0
            while hel + (round_l + 1) * b <= nu_drift_model_one:
                round_l = round_l + 1
                hel = hel + round_l * b
                rest_one = nu_drift_model_one - hel
                rest_two = nu_drift_model_two - hel
            b = b + 1
            rests_one.append(rest_one)
            rests_two.append(rest_two)
            rounds.append(round_l)
        return int(round(rests_one[numpy.argmin(rests_one)] + 0.0001)), int(
            round(rests_two[numpy.argmin(rests_one)] + 0.0001)), rounds[numpy.argmin(rests_one)], numpy.argmin(
            rests_one) + 2


    return rests_one[numpy.argmin(rests_one)], rests_two[numpy.argmin(rests_one)], rounds[numpy.argmin(rests_one)], (
                numpy.argmin(rests_one) * 0.1) + 0.5


def evolve_tree_randomly(previous_process_tree, evolution_stage):
    """ Random change of the process tree

    :param new_process_tree: tree to be changed
    :param evolution_stage: percentage of activities to be affected by the change
    :return: randomly evolved process tree version
    """
    new_process_tree = deepcopy(previous_process_tree)
    acs = count_real_acs(new_process_tree._get_leaves())
    changed_acs = []
    added_acs = []
    deleted_acs = []
    moved_acs = []
    rounds = int(round(acs * evolution_stage + 0.001))
    if rounds == 0:
        rounds = int(numpy.ceil(acs * evolution_stage))
    i = 0
    count = 1
    happen = ""
    while i < rounds:
        happen_be = ""
        ran = randint(1, rounds - i)
        if i == 1:
            ran = randint(1, rounds - i)
        if ran == 1:
            happen_be, worked, count = randomize_tree_one(new_process_tree, happen_be, changed_acs, count)
            while not worked:
                happen_be, worked, count = randomize_tree_one(new_process_tree, happen_be, changed_acs, count)
        elif ran == 2:
            happen_be, worked, count = randomize_tree_two(new_process_tree, happen_be, changed_acs, count)
            while not worked:
                happen_be, worked, count = randomize_tree_two(new_process_tree, happen_be, changed_acs, count)
        elif ran == 3:
            happen_be, worked, count = randomize_tree_three(new_process_tree, happen_be, ran, changed_acs, count)
            while not worked:
                ran = randint(1, rounds - i)
                if ran == 1:
                    ran = randint(1, rounds - i)
                if ran == 1:
                    happen_be, worked, count = randomize_tree_one(new_process_tree, happen_be, changed_acs, count)
                elif ran == 2:
                    happen_be, worked, count = randomize_tree_two(new_process_tree, happen_be, changed_acs, count)
                else:
                    happen_be, worked, count = randomize_tree_three(new_process_tree, happen_be, ran, changed_acs, count)
        else:
            happen_be, worked, count = randomize_tree_more(new_process_tree, happen_be, ran, changed_acs, count)
            while not worked:
                ran = randint(1, rounds - i)
                if ran == 1:
                    ran = randint(1, rounds - i)
                if ran == 1:
                    happen_be, worked, count = randomize_tree_one(new_process_tree, happen_be, changed_acs, count)
                elif ran == 2:
                    happen_be, worked, count = randomize_tree_two(new_process_tree, happen_be, changed_acs, count)
                elif ran == 3:
                    happen_be, worked, count = randomize_tree_three(new_process_tree, happen_be, ran, changed_acs, count)
                else:
                    happen_be, worked, count = randomize_tree_more(new_process_tree, happen_be, ran, changed_acs, count)
        happen_spl = happen_be.split(";")
        last = len(happen_spl)
        happen = happen + happen_spl[last - 2] + "; "
        i = i + ran
        happen_ac = happen.split(';')
        if happen_ac[len(happen_ac)-2].strip() == "activity replaced":
            deleted_acs.append(changed_acs[len(changed_acs)-2])
            added_acs.append(changed_acs[len(changed_acs)-1])
        elif happen_ac[len(happen_ac)-2].strip() == "activity deleted":
            deleted_acs.append(changed_acs[len(changed_acs)-1])
        elif happen_ac[len(happen_ac)-2].strip() == "tree fragment deleted":
            deleted_acs.extend(changed_acs[len(changed_acs)-ran:len(changed_acs)])
        elif happen_ac[len(happen_ac)-2].strip() == "activity added":
            added_acs.append(changed_acs[len(changed_acs)-1])
        elif happen_ac[len(happen_ac)-2].strip() == "activity and operator added":
            added_acs.append(changed_acs[len(changed_acs)-1])
            moved_acs.extend(changed_acs[len(changed_acs)-ran:len(changed_acs)-1])
        else:
            moved_acs.extend(changed_acs[len(changed_acs)-ran:len(changed_acs)])
    return new_process_tree, deleted_acs, added_acs, moved_acs