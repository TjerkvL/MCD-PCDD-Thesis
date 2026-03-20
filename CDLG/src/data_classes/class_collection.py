import os
from copy import deepcopy
from dataclasses import dataclass, field
import pm4py
from pm4py.objects.log.obj import EventLog
from src.data_classes.class_axillary import InfoTypes, TraceAttributes
from src.data_classes.class_drift import DriftInfo
from src.data_classes.class_noise import NoiseInfo
import datetime
import re
import pandas as pd
from src.utilities import extract_list_from_string
from src.utilities import remove_duplicates

from src.utilities import Log_attr_params

@dataclass
class Collection:
    """
    Object for keeping information about added drift and noise instances for a generated event log collection. This class
    allows to parse through a collection of logs (set of log or csv file with log information) and to extract and store all
    the drfit and noise instances from the logs in list and csv files
    """

    drifts: list = field(default_factory=list)
    noise: list = field(default_factory=list)
    number_of_drifts: int = 0
    number_of_noises: int = 0
    TP: int = 0
    FP: int = 0
    FN: int = 0


    def add_drift(self, instance: DriftInfo):
        self.drifts.append(instance)
        self.increase_drift_count()

    def add_drift_from_xes(self, list_drift_per_log: list):
        self.drifts.append(list_drift_per_log)
        self.increase_drift_count_from_xes(list_drift_per_log)

    def add_noise(self, instance: NoiseInfo):
        self.noise.append(instance)
        self.increase_noise_count()

    def increase_drift_count(self):
        self.number_of_drifts += 1

    def increase_drift_count_from_xes(self, list_drift_per_log:list):
        self.number_of_drifts += len(list_drift_per_log)

    def increase_noise_count(self):
        self.number_of_noises += 1

    def fill_drift_log(self):
        # This method is used to store the dictionary with log attribute levels in the log (xes file)
        param_drift = vars(DriftInfo)

    def extract_drift_info_from_log(self, log:EventLog, log_name:str):
        """
        Generates a drift instance from a log file
        :param log(EventLog): stores a log
        :param log_name(str): contains the name of a log
        """
        drift_info_list = []
        for k in list(log.attributes[Log_attr_params.drift_info][
                          Log_attr_params.children].keys()):  # parses through the drifts: k takes k, drift_2 ...
            DI = DriftInfo()
            DI.set_log_id(log_name)
            DI.set_drift_id(k)
            DI.set_process_perspective(
                log.attributes[Log_attr_params.drift_info][Log_attr_params.children][k][Log_attr_params.children][
                    Log_attr_params.process_perspective])
            DI.set_drift_type(
                log.attributes[Log_attr_params.drift_info][Log_attr_params.children][k][Log_attr_params.children][
                    Log_attr_params.drift_type])
            for c in list(
                    log.attributes[Log_attr_params.drift_info][Log_attr_params.children][k][Log_attr_params.children][
                        Log_attr_params.change_info][
                        Log_attr_params.children].keys()):
                DI.add_change_info(
                    [int(i) for i in re.findall(r'\d+',
                                                log.attributes[Log_attr_params.drift_info][Log_attr_params.children][k][
                                                    Log_attr_params.children][
                                                    Log_attr_params.change_info][Log_attr_params.children][c][
                                                    Log_attr_params.children][Log_attr_params.change_trace_index])],
                    log.attributes[Log_attr_params.drift_info][Log_attr_params.children][k][Log_attr_params.children][
                        Log_attr_params.change_info][Log_attr_params.children][c][
                        Log_attr_params.children][Log_attr_params.change_type],
                    log.attributes[Log_attr_params.drift_info][Log_attr_params.children][k][Log_attr_params.children][
                        Log_attr_params.change_info][Log_attr_params.children][c][
                        Log_attr_params.children][Log_attr_params.process_tree_before],
                    log.attributes[Log_attr_params.drift_info][Log_attr_params.children][k][Log_attr_params.children][
                        Log_attr_params.change_info][Log_attr_params.children][c][
                        Log_attr_params.children][Log_attr_params.process_tree_after],  # pb with process tree output
                    log.attributes[Log_attr_params.drift_info][Log_attr_params.children][k][Log_attr_params.children][
                        Log_attr_params.change_info][Log_attr_params.children][c][
                        Log_attr_params.children][Log_attr_params.activities_deleted],
                    log.attributes[Log_attr_params.drift_info][Log_attr_params.children][k][Log_attr_params.children][
                        Log_attr_params.change_info][Log_attr_params.children][c][
                        Log_attr_params.children][Log_attr_params.activities_added],
                    log.attributes[Log_attr_params.drift_info][Log_attr_params.children][k][Log_attr_params.children][
                        Log_attr_params.change_info][Log_attr_params.children][c][
                        Log_attr_params.children][Log_attr_params.activities_moved])
                DI.convert_change_trace_index_into_timestamp(log)

            drift_info_list.append(DI)
        self.add_drift_from_xes(drift_info_list)

        return None
        # extract info xes should return an istance of the class drift_info
        # the variable drifts later on should return contain list of drifts class instances

    def extract_noise_info_from_log(self, log:EventLog):
        """
        Generates a noise instance from a log file
        :param log(EventLog): Stores a log
        """
        NI = NoiseInfo()
        for attr, val in log.attributes["noise:info"]["children"].items():
            if attr == "log_id":
                NI.set_log_id(val)
            elif attr == "noisy_trace_prob":
                NI.set_noisy_trace_prob(val)
            elif attr == "noisy_event_prob":
                NI.set_noisy_event_prob(val)
        self.add_noise(NI)
        return None

    @staticmethod
    def load_log_names_and_paths(path:str):
        """
        Loads all the log names and paths of the log files in a folder
        :param path(str):contains the path of a folder that contains a collection of logs
        """
        """Loads
            Args:
                path(str):
            Returns:
                Dict[str,str]
            Example:
            >>> Collection.load_log_names_and_paths('C:/Users/username/OneDrive/Bureau/Process Mining Git/output/default_JK_1687271372 detected')
            >>> {'log_1_1687271372.xes': 'C:/Users/username/OneDrive/Bureau/Process Mining Git/output/default_JK_1687271372 detected', 'log_2_1687271374.xes': 'C:/Users/ziedk/OneDrive/Bureau/Process Mining Git/output/default_JK_1687271372 detected'}
        """
        loaded_event_logs = {}
        for dir_path, dir_names, filenames in os.walk(path):
            for index, filename in enumerate(filenames):
                if filename.endswith('.xes'):
                    loaded_event_logs[filename] = os.sep.join([dir_path])
        return loaded_event_logs

    def Extract_collection_of_drifts(self, path):
        for log_name, log_folder in self.load_log_names_and_paths(path).items():
            log = pm4py.read_xes(os.path.join(log_folder, log_name))
            self.extract_drift_info_from_log(log, log_name)

    def import_drift_and_noise_info_from_flat_file_csv(self, path:str):
        """
        Generate a collection of logs from a csv file storing log information
        :param path(str): a path to a csv file
        """
        df = pd.read_csv(path, sep=";")

        # 1st: extract all distinct log names
        log_names = remove_duplicates([ln.split(",")[0] for ln in df["log_name"]])
        for log_name in log_names:
            sub_DI = list()
            sub_df_log = df.loc[df["log_name"] == log_name]
            drift_noise_id = remove_duplicates(sub_df_log["drift_or_noise_id"])
            format_string = "%Y-%m-%d %H:%M:%S.%f"
            for id in drift_noise_id:
                sub_df_id = sub_df_log.loc[sub_df_log["drift_or_noise_id"] == id]
                if (id.split("_")[0] == "drift"):
                    change_info_id = remove_duplicates(
                        list(sub_df_id[sub_df_id['drift_attribute'].str.contains(r'change_')]["drift_attribute"]))

                    DI = DriftInfo()
                    NI = NoiseInfo()

                    for change_id in change_info_id:
                        try:  # Some logs do not contain change_start and change_end !!!!
                            change_start = sub_df_id["value"].loc[
                                (sub_df_id["drift_sub_attribute"] == "change_start") & (
                                        sub_df_id["drift_or_noise_id"] == id) & (
                                        sub_df_id["drift_attribute"] == change_id)].values[0]
                            change_end = sub_df_id["value"].loc[(sub_df_id["drift_sub_attribute"] == "change_end") & (
                                    sub_df_id["drift_or_noise_id"] == id) & (sub_df_id[
                                                                                 "drift_attribute"] == change_id)].values[
                                0]
                            change_start = datetime.datetime.strptime(change_start, format_string)
                            change_end = datetime.datetime.strptime(change_end, format_string)

                        except:
                            change_start = None
                            change_end = None

                        # TODO: change the parameters names
                        DI.set_log_id(log_name)
                        DI.set_drift_id(sub_df_id["drift_or_noise_id"].loc[
                                            (sub_df_id["drift_attribute"] == "drift_id") & (
                                                    sub_df_id["drift_or_noise_id"] == id)].values[0])
                        DI.set_process_perspective(sub_df_id["value"].loc[
                                                       (sub_df_id["drift_attribute"] == "process_perspective") & (
                                                               sub_df_id["drift_or_noise_id"] == id)].values[0])
                        DI.set_drift_type(sub_df_id["value"].loc[(sub_df_id["drift_attribute"] == "drift_type") & (
                                sub_df_id["drift_or_noise_id"] == id)].values[0])

                        DI.add_change_info_from_csv(extract_list_from_string(sub_df_id["value"].loc[(sub_df_id[
                                                                                                         "drift_sub_attribute"] == "change_trace_index") & (
                                                                                                            sub_df_id[
                                                                                                                "drift_or_noise_id"] == id) & (
                                                                                                            sub_df_id[
                                                                                                                "drift_attribute"] == change_id)].values[
                                                                                 0]),
                                                    sub_df_id["value"].loc[
                                                        (sub_df_id["drift_sub_attribute"] == "change_type") & (
                                                                sub_df_id["drift_or_noise_id"] == id) & (
                                                                sub_df_id["drift_attribute"] == change_id)].values[
                                                        0],
                                                    sub_df_id["value"].loc[
                                                        (sub_df_id["drift_sub_attribute"] == "process_tree_before") & (
                                                                sub_df_id["drift_or_noise_id"] == id) & (
                                                                sub_df_id["drift_attribute"] == change_id)].values[
                                                        0],
                                                    sub_df_id["value"].loc[
                                                        (sub_df_id["drift_sub_attribute"] == "process_tree_after") & (
                                                                sub_df_id["drift_or_noise_id"] == id) & (
                                                                sub_df_id["drift_attribute"] == change_id)].values[
                                                        0],
                                                    sub_df_id["value"].loc[
                                                        (sub_df_id["drift_sub_attribute"] == "activities_deleted") & (
                                                                sub_df_id["drift_or_noise_id"] == id) & (
                                                                sub_df_id["drift_attribute"] == change_id)].values[
                                                        0],
                                                    sub_df_id["value"].loc[
                                                        (sub_df_id["drift_sub_attribute"] == "activities_added") & (
                                                                sub_df_id["drift_or_noise_id"] == id) & (
                                                                sub_df_id["drift_attribute"] == change_id)].values[
                                                        0],
                                                    sub_df_id["value"].loc[
                                                        (sub_df_id["drift_sub_attribute"] == "activities_moved") & (
                                                                sub_df_id["drift_or_noise_id"] == id) & (
                                                                sub_df_id["drift_attribute"] == change_id)].values[
                                                        0],
                                                    change_start,
                                                    change_end)


                    sub_DI.append(DI)


                elif (id.split("_")[0] == "noise"):
                    NI.set_log_id(log_name)
                    NI.set_noisy_trace_prob(
                        sub_df_log["value"].loc[sub_df_log["drift_sub_attribute"] == "noisy_trace_prob"].values[0])
                    NI.set_noisy_event_prob(
                        sub_df_log["value"].loc[sub_df_log["drift_sub_attribute"] == "noisy_event_prob"].values[0])
                    self.add_noise(NI)

            self.add_drift_from_xes(sub_DI)

        return None


    def export_drift_and_noise_info_to_flat_file_csv(self, path:str):
        """
        Generate a csv file that stores the data of a set of logs
        :param path(str): Path to a location where the resulting csv file should be stored
        """

        dict_nested = dict()
        for drift in self.drifts:
            for attr_key, attr_value in vars(drift).items():
                drift_label = 'drift_' + str(drift.drift_id)
                if isinstance(attr_value, dict):
                    count = 1
                    for attr, value in attr_value.items():
                        if isinstance(value, dict):
                            dict_nested[drift.log_id, drift_label, attr_key + '_' + str(count)] = value
                        else:
                            dict_nested[drift.log_id, drift_label, attr_key + '_' + str(count)] = {attr: value}
                        count += 1
                else:
                    dict_nested[drift.log_id, drift_label, attr_key] = {'na': attr_value}

            # Add noise info
            noise_info_rel = [noise_instance for noise_instance in self.noise if noise_instance.log_id == drift.log_id]
            for index, noise_instance in enumerate(noise_info_rel):
                count = 1
                for attr, value in vars(noise_instance).items():
                    if attr != 'log_id':
                        dict_nested[drift.log_id, 'noise_' + str(index + 1), 'parameter_' + str(count)] = {attr: value}
                        count += 1

        flat_file = []
        for key, values in dict_nested.items():
            for k, v in values.items():
                data = list(key)
                data.extend([k, v])
                flat_file.append(data)

        df = pd.DataFrame(flat_file,
                          columns=['log_name', 'drift_or_noise_id', 'drift_attribute', 'drift_sub_attribute', 'value'])
        df.to_csv(f"{path}/drift_info.csv", index=False, sep=';')
        return None


    def convert_change_trace_index_into_timestamp(self, event_log:EventLog, log_name:str):
        """
        Extract the change timestamps from a log
        :param event_log(EventLog): Stores log data
        :param log_name(str): Stores the log's name
        """
        for drift in self.drifts:
            if drift.log_id == log_name:
                change_info_new = deepcopy(drift.change_info)
                for change_id, change_data in drift.change_info.items():
                    for change_attr, attr_value in change_data.items():
                        if change_attr == 'change_trace_index':
                            if isinstance(attr_value, list) and len(attr_value) == 2:
                                change_info_new[change_id]['change_start'] = event_log[attr_value[0]][0][
                                    TraceAttributes.timestamp.value]
                                change_info_new[change_id]['change_end'] = event_log[attr_value[-1]][0][
                                    TraceAttributes.timestamp.value]
                            elif isinstance(attr_value, list) and len(attr_value) == 1:
                                change_timestamp = event_log[attr_value[0]][0][TraceAttributes.timestamp.value]
                                change_info_new[change_id]['change_start'] = change_timestamp
                                change_info_new[change_id]['change_end'] = change_timestamp
                            else:
                                Warning("Something is wrong!")
                drift.change_info = change_info_new
        return None

    def add_drift_info_to_log(self, event_log:EventLog, log_name:str)->EventLog:
        """

        :param event_log(EventLog): Initial event log without drift
        :param log_name(str): Name of an event log
        :return(EventLog): Return a modified version of the event log that contains drifts
        """
        # TODO: make sure that drift info is added to the log for drift id 0
        output_dict_all_drifts = {'value': 'temp', 'children': {}}
        for drift in self.drifts:
            if drift.log_id == log_name:
                output_dict_drift = dict()
                output_dict_drift.update({'value': drift.drift_id, 'children': {}})
                attr_for_export = ['process_perspective', 'drift_type', 'process_trees', 'change_info']
                for key, value in vars(drift).items():
                    if key in attr_for_export:
                        if isinstance(value, dict):
                            if key == 'change_info':
                                output_dict_drift['children']['change_info'] = {'value': len(value), 'children': {}}
                                for k, v in value.items():
                                    output_dict_drift['children']['change_info']['children'].update(
                                        {'change_id_' + str(k): {'value': 'info', 'children': v}})
                        else:
                            output_dict_drift['children'].update({key: value})

                output_dict_all_drifts['children']['drift_' + str(drift.drift_id)] = output_dict_drift

        event_log.attributes[InfoTypes.drift_info.value] = output_dict_all_drifts

        return event_log


def multiprocessing_info_aggregation(collection_list):
    collection = Collection()
    for (drift_list, noise_instance) in collection_list:
        if drift_list:
            for drift_instance in drift_list:
                collection.add_drift(drift_instance)
        if noise_instance:
            collection.add_noise(noise_instance[0])
    return collection
