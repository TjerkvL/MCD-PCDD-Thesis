from pm4py.objects.log.obj import EventLog
from pm4py.objects.process_tree.obj import ProcessTree

from src.concept_drifts.gradual_drift import additional_gradual_drift_in_log, gradual_drift
from src.concept_drifts.incremental_drift import log_with_incremental_drift_two_models_random, \
    log_with_incremental_drift_two_models_imported, additional_incremental_drift_in_log, \
    additional_incremental_drift_in_log_imported
from src.concept_drifts.recurring_drift import additional_recurring_drift_in_log, recurring_drift
from src.concept_drifts.sudden_drift import sudden_drift, additional_sudden_drift_in_log
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from src.utilities import generate_log_from_tree
from src.controllers.control_flow_controller import change_tree_on_control_flow
from src.controllers.event_log_controller import get_num_trace, get_timestamp_log
from src.controllers.input_controller import input_int, input_drift, input_percentage, input_typ_gradual, \
    generate_tree_out_of_file, input_int_hun, input_yes_no, input_im, input_tree_one, input_comp, \
    input_season, input_percentage_end
from src.controllers.noise_controller import add_noise_to_log
from src.controllers.process_tree_controller import generate_specific_trees
import datetime


def generate_logs_with_models(tree_one, tree_two, incremental_ran, out_file, parameters=None):
    """ Generation of event logs with different concept drifts from two models

    :param parameters: the possible changed parameters for the generation of random process trees
    :param incremental_ran: boolean if incremental drift with random process trees
    :param tree_one: first process tree
    :param tree_two: second process tree
    """
    datestamp = datetime.datetime.strptime('20/23/8 8:0:0',
                                           '%y/%d/%m %H:%M:%S')
    # input_date("Starting date of the first trace in the event log (y/d/m H:M:S like '20/23/8 8:0:0'): ")
    trace_exp_arrival_sec = 7200  # input_int("Minimum for the duration of the activities in the event log in seconds (int): ")
    task_exp_duration_sec = 72000  # input_int_max("Maximum for the duration of the activities in the event log in seconds (int): ",
    # min_duration)

    print("\n--- INPUT DRIFT ---")
    drift_type = input_drift("Type of concept drift [sudden, gradual, recurring, incremental]: ")
    log = EventLog()
    dr_s = "drift perspective: control-flow; "
    start_trace = 0
    end_trace = 0
    drift_info = {}

    if drift_type == 'sudden':
        num_traces = input_int_hun("Number of traces in the event log (x >= 100): ")
        drift_time = input_percentage("starting point of the drift (0 < x < 1): ")
        dr_s += "drift type: sudden; "
        start_trace = get_num_trace(num_traces, drift_time)
        log = sudden_drift(tree_one, tree_two, num_traces, drift_time)

    elif drift_type == 'gradual':
        num_traces = input_int_hun("Number of traces in the event log (x >= 100): ")
        start_point = input_percentage("Starting point of the drift (0 < x < 1): ")
        end_point = input_percentage_end("Ending point of the drift (" + str(start_point) + "0 < x < 1): ", start_point)
        distribution_type = input_typ_gradual(
            "Method for distributing the traces during the gradual drift [linear, exponential]: ")
        dr_s += "drift type: gradual; drift specific information: " + distribution_type + " distribution; "
        start_trace = get_num_trace(num_traces, start_point)
        end_trace = get_num_trace(num_traces, end_point)
        log = gradual_drift(tree_one, tree_two, num_traces, start_point, end_point,
                            distribution_type)

    elif drift_type == 'recurring':
        num_traces = input_int_hun("Number of traces in the event log (x >= 100): ")
        sector_log = input_yes_no("Do you want the recurring drift to persist throughout the event log [yes, no]? ")
        if sector_log == 'yes':
            start_point = 0
            end_point = 1
            num_seasonal_changes = input_int("Number of seasonal changes of the model versions (int): ")
        else:
            start_point = input_percentage("Starting point of the drift (0 < x < 1): ")
            end_point = input_percentage_end("Ending point of the drift (" + str(start_point) + "0 < x < 1): ",
                                             start_point)
            num_seasonal_changes = input_season(start_point, end_point)
        proportion_first = input_percentage(
            "Proportion of the initial version of the model in the final log (0 < x < 1): ")
        dr_s += "drift type: recurring; drift specific information: " + str(
            num_seasonal_changes) + " seasonal changes; "
        start_trace = get_num_trace(num_traces, start_point)
        end_trace = get_num_trace(num_traces, end_point)
        log = recurring_drift(tree_one, tree_two, num_traces, num_seasonal_changes, proportion_first, start_point,
                              end_point)

    elif drift_type == 'incremental':
        if incremental_ran:
            num_models = input_int("Number of evolving model versions in the event log (int): ")
            log, drift_info = log_with_incremental_drift_two_models_random(tree_one, tree_two, num_models, parameters)
        else:
            num_models = input_int("Number of evolving model versions in the event log (int): ")
            j = 1
            trees = []
            while j <= num_models:
                tree_ev = generate_tree_out_of_file(
                    "File path of the " + str(
                        j) + ". evolved model version, which has to be 'pnml', 'bpmn' or 'ptml' (e.g. 'Data/test_data/bpmn/model_00.bpmn'): ")
                trees.append(tree_ev)
                j = j + 1
            nu_old_model = input_int_hun(
                "Number of traces from the initial model version in the event log (x >= 100): ")
            log_old = generate_log_from_tree(tree_one, nu_old_model)
            log, drift_info = log_with_incremental_drift_two_models_imported(log_old, tree_two, trees, num_models)

    if drift_type != 'incremental':
        drift_info = {'d': dr_s, 't': [start_trace, end_trace]}
    result = add_additional_drift_and_noise_in_log(log, tree_one, tree_two, datestamp, trace_exp_arrival_sec, task_exp_duration_sec,
                                                   drift_info)
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
    :param drift_info: drift info of first drift
    """
    addi_drift = input_yes_no("Do you want to add an additional drift to the event log [yes, no]? ")
    drifts = [drift_info]
    drift_step = 2
    trees = [tree_two]
    tree_ev = ProcessTree()
    tree = ProcessTree()
    while addi_drift == 'yes':
        drift_data = {}

        print("\n--- INFORMATION FOR ADDITIONAL DRIFT IN THE EVENT LOG ---\n"
              "Please note that by incautiously setting parameters the previously created drift can be destroyed.\n"
              "It can be decided whether the additional drift is placed at the end or in the event log.\n"
              "If the additional drift for the sudden, gradual and recurring type is added at the end of the log, the number of traces will change.\n"
              "If incremental drift is selected, the number of traces in the resulting event log may change regardless of whether it is set in or at the end of the event log.\n"
              "For the evolution of the process model version, it can be decided between evolving the first or last imported model, importing an new model, or generating an random model.\n")
        drift_type = input_drift(
            "Type of " + str(
                drift_step) + ". concept drift in the event log [sudden, gradual, recurring, incremental]: ")
        str_imp = input_im(
            "Importing a new model version for the drift, generating a random model or evolving an already existing model [import, random, evolve]: ")
        if str_imp == 'import' and drift_type != 'incremental':
            tree_ev = generate_tree_out_of_file(
                "File path of the model version, which has to be 'pnml', 'bpmn' or 'ptml' (e.g. 'Data/test_data/bpmn/model_00.bpmn'): ")
            tree = tree_one
        elif str_imp == 'random' and drift_type != 'incremental':
            str_clp = input_comp("Complexity of the process tree to be generated [simple, middle, complex]: ")
            tree_ev = generate_specific_trees(str_clp)
        elif str_imp == 'evolve':
            str_tree_kind = input_tree_one(
                "Process model version for the evolution of the additional " + drift_type + " drift [first_version, last_version]: ")
            if str_tree_kind == 'first_version':
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
            nu_models = input_int("Number of evolving versions (int): ")
            if str_imp == 'import':
                j = 1
                trees_one = []
                while j <= nu_models:
                    tree_evo = generate_tree_out_of_file(
                        "File path of the " + str(
                            j) + ". evolved model version, which has to be 'pnml', 'bpmn' or 'ptml' (e.g. 'Data/test_data/bpmn/model_00.bpmn'): ")
                    trees_one.append(tree_evo)
                    j = j + 1
                tree_ev = trees_one[len(trees_one) - 1]
                log, drift_data = additional_incremental_drift_in_log_imported(log, tree_ev, trees_one, nu_models - 1)
            elif str_imp == "random":
                str_clp = input_comp("Complexity of the process tree to be generated [simple, middle, complex]: ")
                j = 1
                trees_one = []
                while j <= nu_models:
                    tree_evo = generate_specific_trees(str_clp)
                    trees_one.append(tree_evo)
                    j = j + 1
                tree_ev = trees_one[len(trees_one) - 1]
                log, drift_data = additional_incremental_drift_in_log_imported(log, tree_ev, trees_one, nu_models - 1)
            else:
                log, tree_ev, drift_data = additional_incremental_drift_in_log(log, tree, nu_models)
        drifts.append(drift_data)
        trees.append(tree_ev)
        drift_step = drift_step + 1
        addi_drift = input_yes_no("Do you want to add an additional drift to the event log [yes, no]? ")

    result, noise_data = add_noise_to_log(log, tree_one)
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
            start_drift) + " (" + str(round(start, 2)) + "); drift end timestamp: " + end_drift
        i += 1
    if noise_data is not None:
        start_noise = get_timestamp_log(result, len(result), noise_data['t'][0])
        end_noise = get_timestamp_log(result, len(result), noise_data['t'][1])
        result.attributes['noise info:'] = "noise proportion: " + str(noise_data['p']) + "; start point: " + str(
            start_noise) + " (" + str(round(noise_data['t'][0], 2)) + "); end point: " + str(end_noise) + " (" + str(
            round(noise_data['t'][1], 2)) + "); noise type: " + noise_data['ty']
    return result
