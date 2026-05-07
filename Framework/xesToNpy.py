from pm4py.objects.log.importer.xes import importer as xes_importer
import numpy as np
import os

def xesToNpy(event_log_folder, output_data_folder, output_trace_ids_folder):
    event_log_files = [f for f in os.listdir(event_log_folder) if f.endswith('.xes')]

    for file in event_log_files:
        event_log_path = os.path.join(event_log_folder, file)
        base_name = file.replace('.xes', '')

        output_data_path = os.path.join(output_data_folder, base_name + ".npy")
        output_trace_ids_path = os.path.join(output_trace_ids_folder, base_name + "_trace_ids.npy")

        event_log = xes_importer.apply(event_log_path)

        activities = set()
        for trace in event_log:
            for event in trace:
                activities.add(event["concept:name"])

        activity_to_id = {act: i for i, act in enumerate(sorted(activities))}

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


xesToNpy(
    r"C:\Users\tjerk\Documents\Git\Uni\MCD-PCDD-Thesis\EventLogs\Synthetic Logs",
    "eventLogs",
    "traceIDs"
)