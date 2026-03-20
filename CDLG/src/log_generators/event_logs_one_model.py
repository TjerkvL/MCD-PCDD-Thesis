from pm4py.objects.log.obj import EventLog
from pm4py.objects.process_tree.obj import ProcessTree

from src.concept_drifts.gradual_drift import additional_gradual_drift_in_log, gradual_drift
from src.concept_drifts.incremental_drift import log_with_incremental_drift_one_model, additional_incremental_drift_in_log
from src.concept_drifts.recurring_drift import additional_recurring_drift_in_log, recurring_drift
from src.concept_drifts.sudden_drift import sudden_drift, additional_sudden_drift_in_log
from pm4py.objects.log.exporter.xes import exporter as xes_exporter

from src.controllers.control_flow_controller import change_tree_on_control_flow
from src.controllers.event_log_controller import get_num_trace, get_timestamp_log
from src.controllers.input_controller import input_drift, input_int, input_percentage, \
    input_typ_gradual, input_int_hun, input_yes_no, input_no_yes, input_tree, input_season, \
    input_percentage_end
from src.controllers.noise_controller import add_noise_to_log
import datetime


def generate_logs_with_model(tree_one, out_file):
    """ Generation of event logs with different concept drifts from one model

    :param tree_one: the initial model version
    """
    datestamp = datetime.datetime.strptime('20/23/8 8:0:0', '%y/%d/%m %H:%M:%S')  # input_date("Starting date of the first trace in the event log (y/d/m H:M:S like '20/23/8 8:0:0'): ")
    Trace_exp_arrival_sec = 40000  # input_int("Minimum for the duration of the activities in the event log in seconds (int): ")
    Task_exp_duration_sec = 500000  # input_int_max("Maximum for the duration of the activities in the event log in seconds (int): ",
    # min_duration)
    print("\n--- INPUT DRIFT ---")
    drift_type = input_drift("Type of concept drift [sudden, gradual, recurring, incremental]: ")
    log = EventLog()
    tree_two = ProcessTree()
    dr_s = "drift perspective: control-flow; "
    start_trace = 0
    end_trace = 0
    deleted_acs = []
    added_acs = []
    moved_acs = []
    drift_info = {}

    if drift_type == 'sudden':
        num_traces = input_int_hun("Number of traces in the event log (x >= 100): ")
        drift_time = input_percentage("Starting point of the drift (0 < x < 1): ")
        tree_two, deleted_acs, added_acs, moved_acs = change_tree_on_control_flow(tree_one)
        dr_s += "drift type: sudden; "
        start_trace = get_num_trace(num_traces, drift_time)
        log = sudden_drift(tree_one, tree_two, num_traces, drift_time)

    elif drift_type == 'gradual':
        num_traces = input_int_hun("Number of traces in the event log (x >= 100): ")
        start_point = input_percentage("Starting point of the drift (0 < x < 1): ")
        end_point = input_percentage_end("Ending point of the drift (" + str(start_point) + "0 < x < 1): ", start_point)
        distribution_type = input_typ_gradual(
            "Method for distributing the traces during the gradual drift [linear, exponential]: ")
        tree_two, deleted_acs, added_acs, moved_acs = change_tree_on_control_flow(tree_one)
        dr_s += "drift type: gradual; drift specific information: " + distribution_type + " distribution; "
        start_trace = get_num_trace(num_traces, start_point)
        end_trace = get_num_trace(num_traces, end_point)
        log = gradual_drift(tree_one, tree_two, num_traces, start_point, end_point, distribution_type)

    elif drift_type == 'recurring':
        num_traces = input_int_hun("Number of traces in the event log (x >= 100): ")
        sector_log = input_yes_no("Do you want the recurring drift to persist throughout the event log [yes, no]? ")
        if sector_log == 'yes':
            start_point = 0
            end_point = 1
            num_seasonal_changes = input_int("Number of seasonal changes of the model versions (int): ")
        else:
            start_point = input_percentage("Starting point of the drift (0 < x < 1): ")
            end_point = input_percentage_end("Ending point of the drift ("+str(start_point)+"0 < x < 1): ", start_point)
            num_seasonal_changes = input_season(start_point, end_point)

        proportion_first = input_percentage(
            "Proportion of the first model version in the drift sector of the log (0 < x < 1): ")
        tree_two, deleted_acs, added_acs, moved_acs = change_tree_on_control_flow(tree_one)
        dr_s += "drift type: recurring; drift specific information: "+str(num_seasonal_changes)+" seasonal changes; "
        start_trace = get_num_trace(num_traces, start_point)
        end_trace = get_num_trace(num_traces, end_point)
        log = recurring_drift(tree_one, tree_two, num_traces, num_seasonal_changes, proportion_first,
                              start_point, end_point)


    elif drift_type == 'incremental':
        num_models = input_int("Number of evolving versions (int): ")
        log, tree_two, drift_info = log_with_incremental_drift_one_model(tree_one, num_models)
    if drift_type != 'incremental':
        acs_data = "activities added: "+str(added_acs)+"; activities deleted: "+str(deleted_acs)+"; activities moved: "+str(moved_acs)
        drift_info = {'d': dr_s, 't': [start_trace, end_trace], 'a': acs_data}
    result = add_additional_drift_and_noise_in_log(log, tree_one, tree_two, datestamp, Trace_exp_arrival_sec, Task_exp_duration_sec, drift_info)
    xes_exporter.apply(result, out_file)
    print("Resulting event log stored as", out_file)


def add_additional_drift_and_noise_in_log(log, tree_one, tree_two, datestamp, min_duration, max_duration, drift_info):
    """ Introduction of additional drift and noise into an event log

    :param log: event log
    :param tree_one: initial process tree version
    :param tree_two: evolved process tree version
    :param datestamp: Starting date of the event log
    :param min_duration: minimum duration of activities
    :param max_duration: maximum duration of activities
    :param drift_info: drift info for first drift
    :return: event log with drifts
    """
    addi_drift = input_no_yes("Do you want to add an additional drift to the event log [yes, no]? ")
    drifts = [drift_info]
    drift_step = 2
    trees = [tree_two]
    tree_ev = ProcessTree()
    while addi_drift == 'yes':
        drift_data = {}
        deleted_acs = []
        added_acs = []
        moved_acs = []
        print("\n--- INFORMATION FOR ADDITIONAL DRIFT IN THE EVENT LOG ---\n"
              "Please note that by incautiously setting parameters the previously created drift can be destroyed.\n"
              "It can be decided whether the additional drift is placed at the end or in the event log.\n"
              "If the additional drift for the sudden, gradual and recurring type is added at the end of the log, the number of traces will change.\n"
              "If incremental drift is selected, the number of traces in the resulting event log may change regardless of whether it is set in or at the end of the event log.\n"
              "For the evolution of the process model version, it can be decided between the initial version or the last evolved version.\n")
        drift_type = input_drift(
            "Type of " + str(
                drift_step) + ". concept drift in the event log [sudden, gradual, recurring, incremental]: ")

        str_tree_kind = input_tree(
            "Process model version for the evolution of the additional " + drift_type + " drift [initial_version, evolved_version]: ")
        if str_tree_kind == 'initial_version':
            tree = tree_one
        else:
            length = len(trees)
            tree = trees[length - 1]
        if drift_type != 'incremental':
            tree_ev, deleted_acs, added_acs, moved_acs = change_tree_on_control_flow(tree)

        if drift_type == 'sudden':
            log, drift_data = additional_sudden_drift_in_log(log, tree_ev)

        elif drift_type == 'gradual':
            log, drift_data = additional_gradual_drift_in_log(log, tree, tree_ev)

        elif drift_type == 'recurring':
            log, drift_data = additional_recurring_drift_in_log(log, tree, tree_ev)

        elif drift_type == 'incremental':
            nu_models = input_int("Number of evolving models (int): ")
            log, tree_ev, drift_data = additional_incremental_drift_in_log(log, tree, nu_models)
        if drift_type != 'incremental':
            drift_data['a'] = "activities added: "+str(added_acs)+"; activities deleted: "+str(deleted_acs) + "; activities moved: " + str(moved_acs)
        drifts.append(drift_data)
        trees.append(tree_ev)
        drift_step = drift_step + 1
        addi_drift = input_yes_no("Do you want to add an additional drift to the event log [yes, no]? ")
    result, noise_data = add_noise_to_log(log, tree_one)

    result = add_change_moments_to_log(result)

    i = 1
    for x in drifts:
        start = int(x['t'][0]) / len(result)
        end = int(x['t'][1]) / len(result)
        start_drift = get_timestamp_log(result, len(result), start)
        if end == 0:
            end_drift = 'N/A'
        else:
            end_drift = str(get_timestamp_log(result, len(result), end)) + " (" + str(round(end, 2)) + ")"

        result.attributes['drift info ' + str(i) + ':'] = str(x['d']) + "drift start timestamp: " + str(
            start_drift) + " (" + str(round(start, 2)) + "); drift end timestamp: " + end_drift + "; " + str(x['a'])
        i += 1

    # Save used process trees as a log-level attribute
    trees.insert(0, tree_one)
    trees_string = convert_trees_to_string(trees)
    result.attributes['process_trees'] = trees_string

    if noise_data is not None:
        start_noise = get_timestamp_log(result, len(result), noise_data['t'][0])
        end_noise = get_timestamp_log(result, len(result), noise_data['t'][1])
        result.attributes['noise info:'] = "noise proportion: " + str(noise_data['p']) + "; start point: " + str(
            start_noise) + " (" + str(round(noise_data['t'][0], 2)) + "); end point: " + str(end_noise) + " (" + str(
            round(noise_data['t'][1], 2)) + "); noise type: " + noise_data['ty']
        result.attributes['noise_process_tree'] = str(noise_data['process_tree'])

    return result

def add_change_moments_to_log(created_log):
    change_moments = {}
    current_model_version = created_log[0].attributes['model:version']
    change_id = 0
    for trace in created_log:
        change_moment = trace[0]['time:timestamp']
        version = trace.attributes['model:version']
        if version != current_model_version:
            change_id += 1
            change_moments['change_' + str(change_id)] = change_moment #.strftime("%Y-%m-%d, %H:%M:%S")
            current_model_version = version

    created_log.attributes['change_moments'] = {"value": "timestamps", "children": change_moments}

    return created_log


def convert_trees_to_string(trees):
    trees_info = {'tree_' + str(trace_id): str(trace) for trace_id, trace in enumerate(trees)}
    trees_string = str()
    for key in trees_info:
        trees_string += key + ': ' + trees_info[key] + '; '
    return trees_string[:-2]