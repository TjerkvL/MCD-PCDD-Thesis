import numpy as np
from xes_parser import load_xes
from feature_builder import build_event_log_array

if __name__ == "__main__":
    log = load_xes("data/Simple_1.xes")

    data, trace_ids = build_event_log_array(log)

    np.save("data/Simple_1.npy", data)
    np.save("data/Simple_1_trace_ids.npy", trace_ids)

    print("Saved dataset + trace mapping")
    print("Shape:", data.shape)

    log = load_xes("data/Intermediate_1.xes")

    data, trace_ids = build_event_log_array(log)

    np.save("data/Intermediate_1.npy", data)
    np.save("data/Intermediate_1_trace_ids.npy", trace_ids)

    print("Saved dataset + trace mapping")
    print("Shape:", data.shape)

    log = load_xes("data/Intermediate_4.xes")

    data, trace_ids = build_event_log_array(log)

    np.save("data/Intermediate_4.npy", data)
    np.save("data/Intermediate_4_trace_ids.npy", trace_ids)

    print("Saved dataset + trace mapping")
    print("Shape:", data.shape)

    log = load_xes("data/Difficult_1.xes")

    data, trace_ids = build_event_log_array(log)

    np.save("data/Difficult_1.npy", data)
    np.save("data/Difficult_1_trace_ids.npy", trace_ids)

    print("Saved dataset + trace mapping")
    print("Shape:", data.shape)

    log = load_xes("data/Difficult_4.xes")

    data, trace_ids = build_event_log_array(log)

    np.save("data/Difficult_4.npy", data)
    np.save("data/Difficult_4_trace_ids.npy", trace_ids)

    print("Saved dataset + trace mapping")
    print("Shape:", data.shape)

    print("Saved dataset + trace mapping")
    print("Shape:", data.shape)
