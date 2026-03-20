import copy

from src.controllers.control_flow_controller import evolve_tree_randomly
from src.utilities import generate_log_from_tree
from src.controllers.input_controller import input_percentage, input_no, input_no_yes, input_per_not_null, input_per_half, \
    input_percentage_end
from src.controllers.process_tree_controller import generate_tree
from src.utilities import add_duration_to_log


def add_noise_randomized_tree(log_total, tree_one):
    """ Introduction of noise into an event log via terminal

    :param log_total: event log
    :param tree_one: process tree to be changed for noise generation
    :return: event log with noise
    """
    print("\n--- INFORMATION FOR THE INTRODUCTION OF NOISE ---\n"
          "The noise will be randomly distributed in the sector to be determined.\n"
          "The proportion of noise for this sector can also be predefined.\n"
          "This gives the possibility to either disguise the drift by placing the noise around/inside the drift"
          " or to fake another drift by placing the noise away from the drift.\n"
          "The following two types of noise exist:\n"
          "\tchanged_model: the initial model version is changed randomly, whereby the proportion of changes in the version can be specified.\n"
          "\trandom_model: a completely new model is used, which means that there is little or no similarity to the other model versions.\n"
          "The created model, which will appear as an image, will be used to generate traces introduced in the event log as noise.\n")
    type_noise = input_no("Type of model for generating the noise [changed_model, random_model]: ")
    start_noise = input_percentage("Start point of noise in the event log (0 <= x <= 1): ")
    end_noise = input_percentage_end("End point of noise in the event log (0 <= x <= 1): ", start_noise)
    pro_noise = input_per_half("Proportion of noise in the set sector of the event log (0 < x < 0.5): ")
    nu_traces = int(
        round(((length_of_log(log_total) * end_noise) - (
                length_of_log(log_total) * start_noise)) * pro_noise + 0.0001))
    if type_noise == 'changed_model':
        drift_tree = copy.deepcopy(tree_one)
        evolution_stage = input_per_not_null(
            "Proportion of the changes in the initial tree version for creating the noise (0 < x < 1): ")
        noise_tree, a, b, c = evolve_tree_randomly(drift_tree, evolution_stage)
        log_noise = generate_log_from_tree(noise_tree, nu_traces)
    else:
        noise_tree = generate_tree(
            {'mode': 8, 'min': 6, 'max': 10, 'sequence': 0.25, 'choice': 0.25, 'parallel': 0.25, 'loop': 0.2, 'or': 0,
             'silent': 0, 'duplicate': 0, 'lt_dependency': 0, 'infrequent': 0.25, 'no_models': 10, 'unfold': 10,
             'max_repeat': 10})
        log_noise = generate_log_from_tree(noise_tree, nu_traces)
    return include_noise_in_log(log_total, log_noise, start_noise, end_noise), {'p': pro_noise, 't': [start_noise, end_noise], 'ty': type_noise, 'process_tree': noise_tree}


def add_noise_to_log(log, tree):
    """ Introduces noise and sets the time input_parameters

    :param log: event log
    :param tree: process tree for noise generation
    :param datestamp: starting date of event log
    :param min_duration: minimum duration of activities
    :param max_duration: maximum duration of activities
    :return: event log with time input_parameters and noise, if desired
    """
    str_noise = input_no_yes("Do you want to add noise to the event log [yes, no]? ")
    if str_noise == 'yes':
        log_with_no, noise_data = add_noise_randomized_tree(log, tree)
        add_duration_to_log(log_with_no)
        return log_with_no, noise_data
    else:
        add_duration_to_log(log)
        return log, None



def add_noise_doc(event_log, tree, pro_noise, type_noise, start_noise, end_noise):
    """ Introduction of noise into an event log for text file generation

    :param event_log: event log
    :param tree: process tree for noise generation
    :param pro_noise: proportion of noise in sector
    :param type_noise: type of noise (i.e. random or changed)
    :param start_noise: start point of noise
    :param end_noise: end point of noise
    :return: event log with noise
    """
    nu_traces = int(
        round(((length_of_log(event_log) * end_noise) - (
                length_of_log(event_log) * start_noise)) * pro_noise + 0.0001))
    if type_noise == 'changed_model':
        drift_tree = copy.deepcopy(tree)
        drift_tree, a, b, c = evolve_tree_randomly(drift_tree, 0.4)
        log_noise = generate_log_from_tree(drift_tree, nu_traces)
    else:
        tree = generate_tree(
            {'mode': 8, 'min': 6, 'max': 10, 'sequence': 0.25, 'choice': 0.25, 'parallel': 0.25, 'loop': 0.2, 'or': 0,
             'silent': 0, 'duplicate': 0, 'lt_dependency': 0, 'infrequent': 0.25, 'no_models': 10, 'unfold': 10,
             'max_repeat': 10})
        log_noise = generate_log_from_tree(tree, nu_traces)
    return include_noise_in_log(event_log, log_noise, start_noise, end_noise)


def add_noise_gs(event_log, tree, pro_noise, type_noise, start_noise, end_noise):
    """ Introduction of noise into an event log for text file generation

    :param event_log: event log
    :param tree: process tree for noise generation
    :param pro_noise: proportion of noise in sector
    :param type_noise: type of noise (i.e. random or changed)
    :param start_noise: start point of noise
    :param end_noise: end point of noise
    :return: event log with noise
    """
    nu_traces = int(
        round(((length_of_log(event_log) * end_noise) - (
                length_of_log(event_log) * start_noise)) * pro_noise + 0.0001))
    if nu_traces == 0:
        return event_log, False
    if type_noise == 'changed_model':
        drift_tree = copy.deepcopy(tree)
        tree_ev, a, b, c = evolve_tree_randomly(drift_tree, 0.4)
        log_noise = generate_log_from_tree(tree_ev, nu_traces)
    else:
        tree = generate_tree(
            {'mode': 8, 'min': 6, 'max': 10, 'sequence': 0.25, 'choice': 0.25, 'parallel': 0.25, 'loop': 0.2, 'or': 0,
             'silent': 0, 'duplicate': 0, 'lt_dependency': 0, 'infrequent': 0.25, 'no_models': 10, 'unfold': 10,
             'max_repeat': 10})
        log_noise = generate_log_from_tree(tree, nu_traces)
    return include_noise_in_log(event_log, log_noise, start_noise, end_noise), True


