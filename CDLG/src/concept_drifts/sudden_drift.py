from src.utilities import generate_log_from_tree
from src.controllers.input_controller import input_percentage, input_int, input_end


def sudden_drift(tree_one, tree_two, nu_traces, change_point):
    """ Generation of an event log with a sudden drift

    :param tree_one: the initial version of the process model
    :param tree_two: the evolved version of the process model
    :param nu_traces: number traces in event log
    :param change_point: change point of the drift
    :return: event log with sudden drift
    """
    log_one_traces = int(round(nu_traces * change_point))
    log_two_traces = nu_traces - log_one_traces
    log_one = generate_log_from_tree(tree_one, log_one_traces)
    log_two = generate_log_from_tree(tree_two, log_two_traces)
    logs_combined = combine_two_logs(log_one, log_two)
    return logs_combined


def additional_sudden_drift_in_log(log, tree_two):
    """ Including an additional sudden drift into an event log

    :param log: event log including a drift
    :param tree_two: evolved tree version
    :return:  event log with an additional sudden drift
    """
    dr_s = "drift perspective: control-flow; drift type: sudden;"
    start_trace = 0
    add_end = input_end("Adding the additional sudden drift at the end of the log or into the log [end, into]? ")
    if add_end == 'into':
        drift_time = input_percentage("Starting point of the drift (0 < x < 1): ")
        start_trace = get_num_trace(len(log), drift_time)
        log_two_traces = (length_of_log(log) - start_trace)
        log_two = generate_log_from_tree(tree_two, log_two_traces)
        result_log = replace_traces_of_log(log, log_two, drift_time)
    else:
        nu_add_traces = input_int(
            "Number of additional traces from the new model to be added at the end of the event log (int): ")
        log_two = generate_log_from_tree(tree_two, nu_add_traces)
        start_trace = len(log)
        result_log = combine_two_logs(log, log_two)
    drift_data = {'d': dr_s, 't': [start_trace, 0]}
    return result_log, drift_data
