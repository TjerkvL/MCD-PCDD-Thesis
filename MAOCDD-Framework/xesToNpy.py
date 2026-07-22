# Imports
from pm4py.objects.log.importer.xes import importer as xes_importer
import numpy as np
import os


def convertXesToNpy(eventLogFolder, outputDataFolder, outputTraceIdsFolder):

    # Get all XES files in the govem folder
    eventLogFiles = [file for file in os.listdir(eventLogFolder) if file.endswith(".xes")]

    for file in eventLogFiles:

        eventLogPath = os.path.join(eventLogFolder, file)
        logName = file.replace(".xes", "")

        outputDataPath = os.path.join(outputDataFolder, logName + ".npy")
        outputTraceIdsPath = os.path.join(outputTraceIdsFolder, logName + "_trace_ids.npy")

        # Import event log
        eventLog = xes_importer.apply(eventLogPath)

        # Mapping the activities

        activities = set()

        for trace in eventLog:
            for event in trace:
                activities.add(event["concept:name"])

        activityToId = {
            activity: index
            for index, activity in enumerate(sorted(activities))
        }

        # Converting the log

        data = []
        traceIds = []

        for traceIndex, trace in enumerate(eventLog):

            previousTimestamp = None
            previousActivityId = -1

            for eventIndex, event in enumerate(trace):

                activity = event["concept:name"]
                timestamp = event["time:timestamp"]

                activityId = activityToId[activity]

                # Next activity
                if eventIndex < len(trace) - 1:

                    nextActivityId = activityToId[
                        trace[eventIndex + 1]["concept:name"]
                    ]

                else:

                    nextActivityId = -1

                # Time difference
                if previousTimestamp is None:
                    timeDifference = 0.0

                else:
                    timeDifference = (timestamp - previousTimestamp).total_seconds()

                previousTimestamp = timestamp

                data.append([
                    previousActivityId,
                    activityId,
                    nextActivityId,
                    timeDifference / 1e6
                ])

                traceIds.append(traceIndex)

                previousActivityId = activityId

        # Convert to numpy arrays
        data = np.array(data, dtype=np.float32)
        traceIds = np.array(traceIds)

        # Save files
        np.save(outputDataPath, data)
        np.save(outputTraceIdsPath, traceIds)

        print(f"Saved processed data to {outputDataPath}")
        print(f"Saved trace IDs to {outputTraceIdsPath}")


convertXesToNpy(
    r"C:\Users\tjerk\Documents\GitHub\MCD-PCDD-Thesis\EventLogs\SemiSynthetic Logs",
    r"MAOCDD-Framework\eventLogs",
    r"MAOCDD-Framework\traceIDs"
)