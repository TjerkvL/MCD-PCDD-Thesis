#Code to concatenate multiple event logs into a single event log
import os
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from pm4py.objects.log.obj import EventLog

def merge_xes_logs(directory_path, output_filename="merged.xes"):
    #Start by getting the .xes files and sorting them
    xes_files = sorted([f for f in os.listdir(directory_path) if f.endswith(".xes")])
    
    merged_log = EventLog()

    for file_name in xes_files:
        file_path = os.path.join(directory_path, file_name)
        print(f"Processing: {file_name}")
        
        log = xes_importer.apply(file_path)
        for trace in log:
            merged_log.append(trace)

    output_path = os.path.join(directory_path, output_filename)
    xes_exporter.apply(merged_log, output_path)
    
    print(f"\nMerged log saved to: {output_path}")


merge_xes_logs(r"C:\Users\tjerk\Documents\GitHub\MCD-PCDD-Thesis\EventLogs\BPIC2015")