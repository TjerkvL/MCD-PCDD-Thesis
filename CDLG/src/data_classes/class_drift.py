from dataclasses import dataclass, field
import numpy as np
from collections import defaultdict
from copy import deepcopy
import re
import datetime
import pm4py
from pm4py.objects.log.obj import EventLog


@dataclass
class DriftInfo:
    """
        Object for keeping information about added drift to a generated event log
    """
    log_id: str = None
    drift_id: int = np.NAN
    process_perspective: str = None
    drift_type: str = None
    process_trees: dict = field(default_factory=lambda: defaultdict(dict))
    change_info: dict = field(default_factory=lambda: defaultdict(dict))

    def set_log_id(self, log_name:str):
        """
            Add a log id to a drift instance
        """
        self.log_id = log_name
        return None

    def set_drift_id(self, drift_id:int):
        """
            Add a drift id to a drift instance
        """
        self.drift_id = drift_id
        return None


    def set_process_perspective(self, process_perspective:str):
        """
            Add a process perspective to a drift instance
        """
        self.process_perspective = process_perspective
        return None

    def set_drift_type(self, drift_type:str):
        """
            Add a drift type to a drift instance
        """
        self.drift_type = drift_type
        return None

    def add_process_tree(self, process_tree:dict):
        """
            Add a process tree to a drift instance
        """
        process_tree_id = str(len(self.process_trees))
        self.process_trees[process_tree_id] = deepcopy(process_tree)
        return None

    def add_change_info_from_csv(self,change_trace_index:list, change_type:str, tree_previous:dict, tree_new:dict, deleted_acs:list, added_acs:list, moved_acs:list, change_start:datetime.datetime, change_end:datetime.datetime):
        """
            Add an information about change moment to a drift instance when the drift class is instatiated from a csv file
        """
        self.add_process_tree(tree_new)
        change_id = str(len(self.change_info) + 1)
        self.change_info[change_id] = {'change_type': change_type,
                                       'change_trace_index': change_trace_index,
                                       'process_tree_before': tree_previous,
                                       'process_tree_after': tree_new,
                                       'activities_deleted': deleted_acs,
                                       'activities_added': added_acs,
                                       'activities_moved': moved_acs,
                                       'change_start': change_start,
                                       'change_end':change_end}
        return None


    def add_change_info(self, change_trace_index:list, change_type:str, tree_previous:dict, tree_new:dict, deleted_acs:list, added_acs:list, moved_acs:list):
        """
            Add an information about change moment to a drift instance when the drift class
        """
        self.add_process_tree(tree_new)
        change_id = str(len(self.change_info)+1)
        self.change_info[change_id] = {'change_type': change_type,
                                       'change_trace_index': change_trace_index,
                                       'process_tree_before': tree_previous,
                                       'process_tree_after': tree_new,
                                       'activities_deleted': deleted_acs,
                                       'activities_added': added_acs,
                                       'activities_moved': moved_acs}
        return None

    def convert_change_trace_index_into_timestamp(self, event_log:EventLog):
        change_info_new = deepcopy(self.change_info)
        for change_id, change_data in self.change_info.items():
            for change_attr, attr_value in change_data.items():

                if change_attr == 'change_trace_index':
                    change_info_new[change_id]['change_start'] = event_log[attr_value[0]][0]['time:timestamp']
                    if isinstance(attr_value, list) and len(attr_value) == 2:
                        change_info_new[change_id]['change_end'] = event_log[attr_value[-1]][0]['time:timestamp']
                    elif isinstance(attr_value, list) and len(attr_value) == 1:
                        change_info_new[change_id]['change_end'] = change_info_new[change_id]['change_start']
                    else:
                        ValueError("Something is wrong!")
        self.change_info = change_info_new
        return None


    def get_previous_process_tree(self):
        max_process_tree_id = str(max([int(key) for key in self.process_trees.keys()]))
        previous_process_tree = deepcopy(self.process_trees[max_process_tree_id])
        return previous_process_tree



def initialize_drift_instance_from_list(input: list):
    log_id, drift_id, perspective, drift_type, drift_time, added, deleted, moved, trees = input

    drift_instance = DriftInfo()
    if drift_type:
        drift_instance.log_id = log_id
        drift_instance.drift_id = drift_id
        drift_instance.process_perspective = perspective
        drift_instance.drift_type = drift_type
        drift_instance.drift_time = drift_time
        drift_instance.activities_added = added
        drift_instance.activities_deleted = deleted
        drift_instance.activities_moved = moved
        drift_instance.process_trees = trees

    return drift_instance



