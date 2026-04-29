import numpy as np

def build_event_log_array(log):

    activities = set()
    for trace in log:
        for event in trace:
            activities.add(event["concept:name"])

    activity_to_id = {act: i for i, act in enumerate(sorted(activities))}

    data = []
    trace_ids = []  # NEW

    for trace_idx, trace in enumerate(log):
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
            trace_ids.append(trace_idx)  # NEW

    return np.array(data, dtype=np.float32), np.array(trace_ids)