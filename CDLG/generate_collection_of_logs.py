import os
import sys
import time
from multiprocessing import Pool, cpu_count
from src import configurations as config
from src.data_classes.class_input import InputParameters, get_parameters
from src.data_classes.class_collection import Collection, multiprocessing_info_aggregation
from src.drifts.drift_complex import add_recurring_drift, add_incremental_drift
from src.drifts.drift_simple import add_simple_drift
from src.data_classes.class_drift import DriftInfo
from src.data_classes.class_noise import NoiseInfo
from src.controllers.noise_controller_new import insert_noise
from src.utilities import select_random, add_duration_to_log, add_unique_trace_ids, \
    generate_initial_tree, creat_output_folder, generate_log_from_tree, generate_first_event_log_part_from_initial_process_tree
from src.data_classes.class_axillary import InfoTypes, DriftTypes
from pm4py.objects.log.exporter.xes import exporter as xes_exporter


def event_log_generation_engine(log_id, par, collection, out_folder, file_path_to_own_models=None):
    log_name = "log_" + str(log_id) + '_' + str(int(time.time())) + ".xes"
    # SELECT PARAMETERS FOR THE CURRENT LOG
    tree_initial = generate_initial_tree(par.Process_tree_complexity, file_path_to_own_models)
    drift_n = select_random(par.Number_drifts_per_log, option='uniform_int')
    event_log = generate_first_event_log_part_from_initial_process_tree(tree_initial, par, drift_n)
    if drift_n == 0:
        drift_instance = DriftInfo()
        drift_instance.set_log_id(log_name)
        collection.add_drift(drift_instance)
        drift_instance.set_drift_id(0)
        collection.add_drift(drift_instance)
    else:
        for drift_id in range(1, drift_n + 1):
            # Set drift info instance
            # TODO: integrate
            drift_instance = DriftInfo()
            drift_instance.set_log_id(log_name)
            drift_instance.set_drift_id(drift_id)
            drift_instance.set_process_perspective('control-flow')
            drift_type = select_random(par.Drift_types, option='random')
            drift_instance.set_drift_type(drift_type)
            drift_instance.add_process_tree(tree_initial)
            # GENERATE LOG WITH A CERTAIN DRIFT TYPE
            if drift_type == DriftTypes.sudden.value or drift_type == DriftTypes.gradual.value:
                event_log, drift_instance = add_simple_drift(event_log, drift_instance, par, drift_type)
            elif drift_type == DriftTypes.recurring.value:
                event_log, drift_instance = add_recurring_drift(event_log, drift_instance, par)
            elif drift_type == DriftTypes.incremental.value:
                event_log, drift_instance = add_incremental_drift(event_log, drift_instance, par)
            else:
                UserWarning(f'Specified "drift_type" {drift_type} in the parameter file does not exist')

            collection.add_drift(drift_instance)

    # ADD NOISE and CREATE NOISE INFO INSTANCE
    # TODO: integrate the noise related lines below
    noise = select_random(par.Noise, option='random')
    if noise:
        noisy_trace_prob = select_random(par.Noisy_trace_prob, option='random')
        noisy_event_prob = select_random(par.Noisy_event_prob, option='uniform_step')
        noise_instance = NoiseInfo(log_name, noisy_trace_prob, noisy_event_prob)
        event_log = insert_noise(event_log, noise_instance.noisy_trace_prob, noise_instance.noisy_event_prob,
                                 par.Task_exp_duration_sec)
        collection.add_noise(noise_instance)
        event_log.attributes[InfoTypes.noise_info.value] = noise_instance.noise_info_to_dict()


    # ADD TIMESTAMP TO EACH EVENT OF THE LOG
    add_duration_to_log(event_log, par)

    # ADD UNIQUE TRACE IDs
    add_unique_trace_ids(event_log)

    # ADD CHANGE TIMESTAMPS
    collection.convert_change_trace_index_into_timestamp(event_log, log_name)

    # ADD DRIFT INFO TO THE LOG
    event_log = collection.add_drift_info_to_log(event_log, log_name)

    # EXPORT GENERATED LOG
    xes_exporter.apply(event_log, os.path.join(out_folder, log_name))

    return collection


def generate_logs_worker(log_id_par):
    collection = Collection()
    log_id, par, file_path_to_own_models, out_folder, number_of_logs = log_id_par

    collection = event_log_generation_engine(log_id, par, collection, out_folder, file_path_to_own_models)
    print(f"Finished log {log_id} from {number_of_logs}")

    return (collection.drifts, collection.noise)


def multi_processing_generate_logs(par: InputParameters, file_path_to_own_models=None):
    if config.N_CORES is None:
        num_cores = cpu_count() - 2
    else:
        num_cores = config.N_CORES

    out_folder = creat_output_folder(config.DEFAULT_OUTPUT_DIR, par.Folder_name)
    number_of_logs = select_random(par.Number_event_logs)

    print(f'Generating {number_of_logs} logs in {out_folder}')
    collection_list = []
    with Pool(num_cores) as pool:
        log_ids = [(log_id, par, file_path_to_own_models, out_folder, number_of_logs) for log_id in
                   range(1, number_of_logs + 1)]
        for (drifts, noise) in pool.map(generate_logs_worker, log_ids):
            collection_list.append((drifts, noise))

    collection = multiprocessing_info_aggregation(collection_list)
    collection.export_drift_and_noise_info_to_flat_file_csv(path=out_folder)
    print(f'Finished generating collection of {number_of_logs} logs in {out_folder}')

    return None


def single_processing_generate_logs(par: InputParameters, file_path_to_own_models=None):
    """
    Generation of a set of event logs with different drifts, a corresponding CSV file and respective text files
    :param par(InputParameters): is a class storing the parameter used to generate the logs
    :param file_path_to_own_models(str): file path to own process model, if desired to be used
    :return: collection of event logs with drifts saved in out_folder
    """

    # CREATE DIR TO STORE GENERATED LOGS
    out_folder = creat_output_folder(config.DEFAULT_OUTPUT_DIR, par.Folder_name)
    # MAIN LOOP
    number_of_logs = select_random(par.Number_event_logs)
    print('Generating', number_of_logs, 'logs in', out_folder)
    collection = Collection()
    for log_id in range(1, number_of_logs + 1):
        collection = event_log_generation_engine(log_id, par, collection, out_folder, file_path_to_own_models)
        print(f"Finished log {log_id} from {number_of_logs} logs")

    collection.export_drift_and_noise_info_to_flat_file_csv(path=out_folder)
    print('Finished generating collection of', number_of_logs, 'logs in', out_folder)

    return None


def main(parameters):
    if config.MULTIPROCESSING:
        if len(sys.argv) == 1:
            multi_processing_generate_logs(parameters)
        elif len(sys.argv) == 2:
            multi_processing_generate_logs(parameters, sys.argv[1])
    else:
        if len(sys.argv) == 1:
            single_processing_generate_logs(parameters)
        elif len(sys.argv) == 2:
            single_processing_generate_logs(parameters, sys.argv[1])


if __name__ == '__main__':
    # Record start time
    start_time = time.time()

    par = get_parameters(config.PARAMETER_NAME)
    main(par)

    # Report time
    elapsed_time = time.time() - start_time
    seconds = elapsed_time % 60
    minutes = (elapsed_time // 60) % 60
    hours = elapsed_time // 3600
    print(f'Total elapsed time: {hours:.3f} hours, {minutes:.2f} minutes, {seconds:.1f} seconds')

    sys.exit()
