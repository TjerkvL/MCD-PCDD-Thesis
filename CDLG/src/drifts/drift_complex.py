from src.controllers.control_flow_controller import evolve_tree_randomly
from src.utilities import select_random, generate_log_from_tree

from src.drifts.change_type import combine_two_logs_with_certain_change_type
from pm4py.objects.log.obj import EventLog
from src.data_classes.class_drift import DriftInfo
from src.data_classes.class_input import InputParameters


def add_recurring_drift(event_log: EventLog, drift_instance:DriftInfo, par:InputParameters)->tuple:
    """
    Include a recurring drift in the log
    :param event_log(EventLog): Stores an event log
    :param drift_instance(DriftInfo): A class object storing data about a drift
    :param par(InputParameters): A class object storing input parameters used to generate a gradual drift
    :return(Tuple[EventLog,DriftInfo]):A tuple containing an event log with recurring drift and an instance of a drift
    """
    tree_previous = drift_instance.get_previous_process_tree()
    ran_evolve = select_random(par.Process_tree_evolution_proportion, option='uniform')
    tree_new, deleted_acs, added_acs, moved_acs = evolve_tree_randomly(tree_previous, ran_evolve)
    axillary_order_1 = [tree_previous, tree_new, deleted_acs, added_acs, moved_acs]
    axillary_order_2 = [tree_new, tree_previous, added_acs, deleted_acs, moved_acs]

    number_of_seasonal_changes = select_random(par.Recurring_drift_number, option='random')
    for i in range(0, number_of_seasonal_changes):
        if i % 2 == 0:
            event_log, drift_instance = combine_two_logs_with_certain_change_type(event_log, drift_instance, par,
                                                                                  axillary_order_1)
        else:
            event_log, drift_instance = combine_two_logs_with_certain_change_type(event_log, drift_instance, par,
                                                                                  axillary_order_2)

    return event_log, drift_instance





def add_incremental_drift(event_log, drift_instance, par):
    """
    Include an incremental drift in the log
    :param event_log(EventLog): Stores an event log
    :param drift_instance(DriftInfo): A class object storing data about a drift
    :param par(InputParameters): A class object storing input parameters used to generate a gradual drift
    :return(Tuple[EventLog,DriftInfo]):A tuple containing an event log with recurring drift and an instance of a drift
    """

    num_models = select_random(par.Incremental_drift_number, option='random')
    for i in range(1, num_models+1):
        event_log, drift_instance = combine_two_logs_with_certain_change_type(event_log, drift_instance, par)

    return event_log, drift_instance


