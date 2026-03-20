from src.utilities import generate_log_from_tree
from src.controllers.input_controller import input_int, input_percentage, input_end, input_yes_no, input_season


def recurring_drift(tree_one, tree_two, nu_traces, number_of_seasonal_changes, proportion_first, start_point,
                    end_point):
    """ Generation of an event log with a recurring drift

    :param end_point: end change point of the drift
    :param start_point: start change point of the drift
    :param proportion_first: proportion of the initial model version during the drift
    :param tree_one: initial version of the process tree
    :param tree_two: evolved version of the process tree
    :param nu_traces: number of traces in the log
    :param number_of_seasonal_changes: the number of changes of the model versions in the log
    :return: event log with recurring drift
    """
    nu_traces_log_one = int(
        round((nu_traces * start_point) + (nu_traces * ((end_point - start_point) * proportion_first)) + 0.0001))
    nu_traces_log_two = nu_traces - nu_traces_log_one
    log_one = generate_log_from_tree(tree_one, nu_traces_log_one)
    log_two = generate_log_from_tree(tree_two, nu_traces_log_two)
    if start_point == 0:
        nu_occur_one = int(round((number_of_seasonal_changes + 1.1) / 2))
        nu_occur_two = (number_of_seasonal_changes + 1) - nu_occur_one
    else:
        nu_occur_two = int(round((number_of_seasonal_changes + 1.1) / 2))
        nu_occur_one = (number_of_seasonal_changes + 1) - nu_occur_two
    nu_traces_start = int(round(nu_traces * start_point + 0.0001))
    nu_traces_sec_drift = int(
        round((((nu_traces * end_point) - (nu_traces * start_point)) * (1 - proportion_first)) + 0.0001))
    result, log_drift = generate_two_parts_of_event_log(log_one, nu_traces_start)
    sec_drift_log, log_end = generate_two_parts_of_event_log(log_two, nu_traces_sec_drift)
    parts_log_one = generate_several_parts_of_event_log(log_drift, nu_occur_one)
    parts_log_two = generate_several_parts_of_event_log(sec_drift_log, nu_occur_two)
    if start_point == 0:
        result = combine_two_logs(result, parts_log_one[0])
        result = combine_two_logs(result, parts_log_two[0])
        i = 1
        while i < nu_occur_two:
            result = combine_two_logs(result, parts_log_one[i])
            result = combine_two_logs(result, parts_log_two[i])
            i = i + 1
        if nu_occur_two != nu_occur_one:
            result = combine_two_logs(result, parts_log_one[nu_occur_one - 1])
        if end_point != 1:
            result = combine_two_logs(result, log_end)
    else:
        result = combine_two_logs(result, parts_log_two[0])
        result = combine_two_logs(result, parts_log_one[0])
        i = 1
        while i < nu_occur_one:
            result = combine_two_logs(result, parts_log_two[i])
            result = combine_two_logs(result, parts_log_one[i])
            i = i + 1
        if nu_occur_two != nu_occur_one:
            result = combine_two_logs(result, parts_log_two[nu_occur_two - 1])
        if end_point != 1:
            result = combine_two_logs(result, log_end)
    return result


def additional_recurring_drift_in_log(log, tree_one, tree_two):
    """

    :param log: existing event log
    :param tree_one: initial process tree version
    :param tree_two: last evolved process tree version
    :return: log with an additional drift
    """
    add_end = input_end("Adding the additional recurring drift at the end of the log or into the log [end, into]? ")
    dr_s = "drift perspective: control-flow; drift type: recurring; drift specific information: "
    if add_end == 'into':
        sector_log = input_yes_no("Do you want the recurring drift to persist throughout the event log [yes, no]? ")
        if sector_log == 'yes':
            start_point = 0
            end_point = 1
            num_seasonal_changes = input_int("Number of seasonal changes of the models (int): ")
        else:
            start_point = input_percentage("Starting point of the drift (0 < x < 1): ")
            end_point = input_percentage("Ending point of the drift (0 < x < 1): ")
            num_seasonal_changes = input_season(start_point, end_point)
        proportion = input_percentage(
            "Proportion of the previously generated log in the drift sector of the new log (0 < x < 1): ")
        num_traces = length_of_log(log)
        dr_s += str(num_seasonal_changes)+" seasonal changes; "
        start_trace = get_num_trace(num_traces, start_point)
        end_trace = get_num_trace(num_traces, end_point)
        if start_point == 0:
            nu_occur_one = int(round((num_seasonal_changes + 1.1) / 2))
            nu_occur_two = (num_seasonal_changes + 1) - nu_occur_one
        else:
            nu_occur_two = int(round((num_seasonal_changes + 1.1) / 2))
            nu_occur_one = (num_seasonal_changes + 1) - nu_occur_two
        nu_traces_sec_drift = int(
            round((((num_traces * end_point) - (num_traces * start_point)) * (1 - proportion)) + 0.0001))
        log_two = generate_log_from_tree(tree_two, nu_traces_sec_drift)
        parts_log_two = generate_several_parts_of_event_log(log_two, nu_occur_two)
        proportion_part_of_first_log = (end_point - start_point) * (proportion / nu_occur_one)
        proportion_part_of_second_log = (end_point - start_point) * ((1 - proportion) / nu_occur_two)
        log_two_end = generate_log_from_tree(tree_two, int(round(num_traces*(1-end_point))))
        if start_point == 0:
            start = proportion_part_of_first_log
            end = start + proportion_part_of_second_log
            result = replace_traces_of_log(log, parts_log_two[0], start)
            i = 1
            while i < nu_occur_two:
                start = end + proportion_part_of_first_log
                end = start + proportion_part_of_second_log
                result = replace_traces_of_log(result, parts_log_two[i], start)
                i = i + 1
        else:
            start = start_point
            end = start + proportion_part_of_second_log
            result = replace_traces_of_log(log, parts_log_two[0], start)
            i = 1
            while i < nu_occur_two:
                start = end + proportion_part_of_first_log
                end = start + proportion_part_of_second_log
                result = replace_traces_of_log(result, parts_log_two[i], start)
                i = i + 1
        result = replace_traces_of_log(result, log_two_end, end_point)
    else:
        nu_add_traces = input_int("Number of additional traces to be added at the end of the event log (int): ")
        num_seasonal_changes = input_int("Number of seasonal changes of the models (int): ")
        dr_s += str(num_seasonal_changes)+" seasonal changes; "
        start_trace = len(log)
        end_trace = start_trace + nu_add_traces
        proportion_first = input_percentage(
            "Proportion of the traces from the previously model in the drift (0 < x < 1): ")
        log_rec = recurring_drift(tree_two, tree_one, nu_add_traces, num_seasonal_changes, 1-proportion_first, 0, 1)
        result = combine_two_logs(log, log_rec)
    drift_data = {'d': dr_s, 't': [start_trace, end_trace]}
    return result, drift_data
