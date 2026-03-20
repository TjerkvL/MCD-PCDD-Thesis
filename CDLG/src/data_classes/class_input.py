import ast
import datetime
from dataclasses import dataclass, fields

from src import configurations as config


@dataclass
class InputParameters:
    Process_tree_complexity: list
    Process_tree_evolution_proportion: list
    Number_event_logs: list
    Number_traces_per_process_model_version: list
    Number_traces_for_gradual_change: list
    Change_type: list
    Drift_types: list
    Number_drifts_per_log: list
    Noise: list
    Noisy_trace_prob: list
    Noisy_event_prob: list
    Trace_exp_arrival_sec: list
    Task_exp_duration_sec: list
    Gradual_drift_type: list
    Incremental_drift_number: list
    Recurring_drift_number: list
    Folder_name: str



    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key in {field.name for field in fields(InputParameters)}:
                setattr(self, key, value)


def get_parameters(path: str = config.PARAMETER_NAME)->InputParameters:
    """
    Get the parameters to generate the logs
    :param path(str): contains the name of the default parameter file to use
    :return (InputParameters): A class instance that stores the input parameters
    """
    parameters_dict = create_dict_with_input_parameters(path)
    parameters = InputParameters(**parameters_dict)
    return parameters


def create_dict_with_input_parameters(par_file_name: str)->dict():
    """
    Getting parameters from a specific text file placed in the folder 'Data/parameters'
    :param(str) par_file_name: The name of the file that contains the desired parameters
    :return(dict): parameters for the generation of a set of event logs
    """
    parameter_doc = open(f'{config.DEFAULT_PARAMETER_DIR}/{par_file_name}', 'r')
    parameters_input = parameter_doc.read()
    parameter_doc.close()
    parameters_dict = {}
    for line in parameters_input.split('\n'):
        if line:
            par = line.split(': ')[0]
            value = line.split(': ')[1]
            if '/' in value:
                value = [datetime.strptime(v, '%Y/%m/%d %H:%M:%S') for v in value.split(',')]
            elif '-' in value:
                value = value.split('-')
            else:
                value = value.split(', ')

            try:
                value = [ast.literal_eval(v) for v in value]
            except:
                pass
            parameters_dict[par] = value

    parameters_dict['Folder_name'] = config.PARAMETER_NAME

    return parameters_dict
