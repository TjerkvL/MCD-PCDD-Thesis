#Imports
from pm4py.objects.log.importer.xes import importer as xes_importer
import numpy as np

def xesToNpy(event_log_path, output_data_path, output_trace_ids_path):
    '''
    A function to prepare a .xes file for use in the MCD-PCDD framework
    Input: Path to .xes file
       Two output files:
       -Converted .xes file in .npy format, ready to be used for the MCD-PCDD framework
       -Trace IDs corresponding to each event in the processed data, so that drifts may be located by trace ID
    '''
    event_log = xes_importer.apply(event_log_path)

    # Build the list of unique activities in the event log
    activities = set()
    for trace in event_log:
        for event in trace:
            activities.add(event["concept:name"])

    # Create a mapping from activity names to unique integer IDs
    activity_to_id = {act: i for i, act in enumerate(sorted(activities))}

    #Initialize the lists that hold the processed data and trace IDs
    data = []
    trace_ids = []

    for trace_idx, trace in enumerate(event_log):
        prev_time = None

        for event in trace:
            activity = event["concept:name"]
            timestamp = event["time:timestamp"]

            activity_id = activity_to_id[activity]

            if prev_time is None:
                delta = 0.0
            else:
                delta = (timestamp - prev_time).total_seconds()

            prev_time = timestamp

            data.append([activity_id, delta / 1e6])
            trace_ids.append(trace_idx)
    
    data  = np.array(data, dtype=np.float32)
    trace_ids = np.array(trace_ids)

    np.save(output_data_path, data)
    np.save(output_trace_ids_path, trace_ids)

    print(f"Saved processed data to {output_data_path}")
    print(f"Saved trace IDs to {output_trace_ids_path}")


xesToNpy(r"C:\Users\tjerk\Documents\GitHub\MCD-PCDD-Thesis\EventLogs\Synthetic Logs\Intermediate_1.xes",
          "eventLogs/Intermediate_1.npy",
            "traceIDs/Intermediate_1_trace_ids.npy")