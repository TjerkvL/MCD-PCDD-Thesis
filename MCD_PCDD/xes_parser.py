from pm4py.objects.log.importer.xes import importer as xes_importer


def load_xes(path):
    """
    Load a .xes event log file.

    Returns:
        log: pm4py EventLog object
    """
    log = xes_importer.apply(path)
    return log


def log_summary(log):
    """
    Print a simple summary of the log.
    """
    num_traces = len(log)
    num_events = sum(len(trace) for trace in log)

    print(f"Number of traces: {num_traces}")
    print(f"Total events: {num_events}")

    # Peek at first trace
    first_trace = log[0]
    print("\nFirst trace example:")
    for event in first_trace[:5]:
        print(event)