# Imports
import os
import numpy as np
import matplotlib.pyplot as plt


def EvaluatePerformance(
    methodResultsList,
    methodNames,
    actualDriftCoords,
    allowEarlyDetection,
    lagWindow=50,
    plot=True,
    saveFolder="evaluation_plots"
):

    # Check if provided lists have matching lengths
    if len(methodResultsList) != len(methodNames):
        raise ValueError("methodResultsList and methodNames must have equal length.")

    if len(allowEarlyDetection) != len(methodNames):
        raise ValueError("allowEarlyDetection must have the same length as methodNames.")

    os.makedirs(saveFolder, exist_ok=True)

    # Assign a unique color to each method
    colorMap = plt.get_cmap("tab10")

    methodColors = {
        methodNames[i]: colorMap(i % 10)
        for i in range(len(methodNames))
    }

    # Store results from all methods
    allResults = {}

    overallF1Scores = []
    overallPrecisions = []
    overallRecalls = []
    overallLatencies = []


    for methodIndex, detectedDriftCoords in enumerate(methodResultsList):

        methodName = methodNames[methodIndex]
        allowEarly = allowEarlyDetection[methodIndex]

        print("\n" + "=" * 80)
        print(f"METHOD: {methodName}")
        print("=" * 80)

        results = {}

        allF1Scores = []
        allPrecisionScores = []
        allRecallScores = []
        allLatencies = []


        # Evaluate every log individually
        for logName in actualDriftCoords:

            actualDrifts = sorted(actualDriftCoords[logName])
            detectedDrifts = sorted(detectedDriftCoords.get(logName, []))

            matchedActual = set()
            matchedDetected = set()

            latencies = []


            # Match detected drifts with actual drifts
            for actualIndex, actualDrift in enumerate(actualDrifts):

                bestDistance = float("inf")
                bestDetectedIndex = None

                for detectedIndex, detectedDrift in enumerate(detectedDrifts):

                    if detectedIndex in matchedDetected:
                        continue

                    distance = detectedDrift - actualDrift

                    if allowEarly:

                        if abs(distance) <= lagWindow and abs(distance) < bestDistance:
                            bestDistance = abs(distance)
                            bestDetectedIndex = detectedIndex

                    else:

                        if 0 <= distance <= lagWindow and distance < bestDistance:
                            bestDistance = distance
                            bestDetectedIndex = detectedIndex

                if bestDetectedIndex is not None:

                    matchedActual.add(actualIndex)
                    matchedDetected.add(bestDetectedIndex)
                    latencies.append(bestDistance)


            # Calculate classification metrics
            truePositives = len(matchedActual)
            falsePositives = len(detectedDrifts) - truePositives
            falseNegatives = len(actualDrifts) - truePositives

            precision = (
                truePositives / (truePositives + falsePositives)
                if (truePositives + falsePositives) > 0
                else 0
            )

            recall = (
                truePositives / (truePositives + falseNegatives)
                if (truePositives + falseNegatives) > 0
                else 0
            )

            f1Score = (
                2 * precision * recall / (precision + recall)
                if (precision + recall) > 0
                else 0
            )

            averageLatency = np.mean(latencies) if latencies else None

            results[logName] = {
                "F1-score": f1Score,
                "Precision": precision,
                "Recall": recall,
                "TP": truePositives,
                "FP": falsePositives,
                "FN": falseNegatives,
                "Avg Latency": averageLatency
            }

            allF1Scores.append(f1Score)
            allPrecisionScores.append(precision)
            allRecallScores.append(recall)

            if latencies:
                allLatencies.extend(latencies)


            # Print individual results
            print(f"\n{logName}")
            print("-" * 40)
            print(f"F1-score     : {f1Score:.4f}")
            print(f"Precision    : {precision:.4f}")
            print(f"Recall       : {recall:.4f}")
            print(f"TP / FP / FN : {truePositives} / {falsePositives} / {falseNegatives}")

            if averageLatency is not None:
                print(f"Avg Latency  : {averageLatency:.2f}")
            else:
                print("Avg Latency  : None")


        overallF1 = np.mean(allF1Scores)
        overallPrecision = np.mean(allPrecisionScores)
        overallRecall = np.mean(allRecallScores)
        overallLatency = np.mean(allLatencies) if allLatencies else None

        results["OVERALL"] = {
            "Average F1-score": overallF1,
            "Average Precision": overallPrecision,
            "Average Recall": overallRecall,
            "Average Latency": overallLatency
        }


        print("\n--- OVERALL ---")
        print(f"Average F1-score  : {overallF1:.4f}")
        print(f"Average Precision : {overallPrecision:.4f}")
        print(f"Average Recall    : {overallRecall:.4f}")

        if overallLatency is not None:
            print(f"Average Latency   : {overallLatency:.2f}")
        else:
            print("Average Latency   : None")


        # Store results
        allResults[methodName] = results

        overallF1Scores.append(overallF1)
        overallPrecisions.append(overallPrecision)
        overallRecalls.append(overallRecall)
        overallLatencies.append(overallLatency if overallLatency is not None else 0)


    if plot:
        barColors = [
            methodColors[methodName]
            for methodName in methodNames
        ]


        plt.figure(figsize=(10, 6))

        plt.bar(
            methodNames,
            overallF1Scores,
            color=barColors,
            width=0.5
        )

        plt.ylim(0, 0.75)
        plt.title("Average F1-score per Method")
        plt.ylabel("Average F1-score")
        plt.xticks(rotation=15)

        plt.tight_layout()

        plt.savefig(
            os.path.join(saveFolder, "average_f1_scores.png"),
            dpi=300,
            bbox_inches="tight"
        )

        plt.close()


        plt.figure(figsize=(10, 6))

        plt.bar(
            methodNames,
            overallPrecisions,
            color=barColors,
            width=0.5
        )

        plt.ylim(0, 0.75)
        plt.title("Average Precision per Method")
        plt.ylabel("Average Precision")
        plt.xticks(rotation=15)

        plt.tight_layout()

        plt.savefig(
            os.path.join(saveFolder, "average_precision_scores.png"),
            dpi=300,
            bbox_inches="tight"
        )

        plt.close()


        plt.figure(figsize=(10, 6))

        plt.bar(
            methodNames,
            overallRecalls,
            color=barColors,
            width=0.5
        )

        plt.ylim(0, 0.75)
        plt.title("Average Recall per Method")
        plt.ylabel("Average Recall")
        plt.xticks(rotation=15)

        plt.tight_layout()

        plt.savefig(
            os.path.join(saveFolder, "average_recall_scores.png"),
            dpi=300,
            bbox_inches="tight"
        )

        plt.close()


        plt.figure(figsize=(10, 6))

        plt.bar(
            methodNames,
            overallLatencies,
            color=barColors,
            width=0.5
        )

        plt.title("Average Latency per Method")
        plt.ylabel("Average Latency")
        plt.xticks(rotation=15)

        plt.tight_layout()

        plt.savefig(
            os.path.join(saveFolder, "average_latencies.png"),
            dpi=300,
            bbox_inches="tight"
        )

        plt.close()

        print("\nPlots saved to:")
        print(saveFolder)


    return allResults


# Drift coordinates

# Coupling file names with their actual drift trace numbers

actualDriftCoords = {
    "Simple_1.xes": [1000],
    "Simple_2.xes": [666],
    "Simple_3.xes": [666, 1333],
    "Simple_4.xes": [500, 1500],

    "Intermediate_1.xes": [666, 1333],
    "Intermediate_2.xes": [800, 1200],
    "Intermediate_3.xes": [666, 1333],
    "Intermediate_4.xes": [800, 1200],

    "Difficult_1.xes": [400, 800, 1200],
    "Difficult_2.xes": [400, 600, 800],
    "Difficult_3.xes": [400, 800, 1200],
    "Difficult_4.xes": [400, 600, 800],

    "BPIC2015Merged.xes": [1079, 1948, 3299, 4388]
}


# Dictionary of the results to be evaluated, coupling the file name with the list of detected drift locations

deSousaCoords = {
    "Simple_1.xes" : [341, 681, 903, 1139],
    "Simple_2.xes" : [294, 1124, 1649],
    "Simple_3.xes" : [374],
    "Simple_4.xes" : [194, 947],
    "Intermediate_1.xes" : [384, 542, 718, 1934],
    "Intermediate_2.xes" : [152, 670, 1844],
    "Intermediate_3.xes" : [374],
    "Intermediate_4.xes" : [194, 947],
    "Difficult_1.xes" : [251, 534, 879, 1235, 1734],
    "Difficult_2.xes" : [292, 457, 765],
    "Difficult_3.xes" : [181, 565, 842, 1478, 1851],
    "Difficult_4.xes" : [252, 568],
    "BPIC2015Merged.xes" : [
        396, 1047, 1226, 1465, 2037,
        2457, 2960, 3446, 3677, 4195,
        4413
    ]
}


hueteCoords = {
    "Simple_1.xes" : [609, 817, 1062],
    "Simple_2.xes" : [604, 995, 1631],
    "Simple_3.xes" : [779, 1304, 1935],
    "Simple_4.xes" : [410],
    "Intermediate_1.xes" : [],
    "Intermediate_2.xes" : [1129, 1381],
    "Intermediate_3.xes" : [352, 689, 1382],
    "Intermediate_4.xes" : [468, 1327, 1748],
    "Difficult_1.xes" : [928, 1268],
    "Difficult_2.xes" : [188, 862],
    "Difficult_3.xes" : [1550],
    "Difficult_4.xes" : [527, 791],
    "BPIC2015Merged.xes" : [
        901, 1089, 1170, 1191, 1207, 1224,
        1260, 1460, 1508, 1553, 1599, 1624,
        1659, 1837, 1863, 1948, 2188, 2227,
        2260, 2329, 2495, 2511, 4549, 5636
    ]
}


martjushevCoords = {
    "Simple_1.xes" : [998],
    "Simple_2.xes" : [97, 728, 867, 1081, 1150],
    "Simple_3.xes" : [666, 1164, 1529, 1816],
    "Simple_4.xes" : [495, 1003],
    "Intermediate_1.xes" : [1301],
    "Intermediate_2.xes" : [],
    "Intermediate_3.xes" : [677, 1330],
    "Intermediate_4.xes" : [794, 1032, 1194],
    "Difficult_1.xes" : [401, 1221],
    "Difficult_2.xes" : [397, 548, 786],
    "Difficult_3.xes" : [760],
    "Difficult_4.xes" : [375, 609, 792]
}


MCDPCDDCoords = {
    "Simple_1.xes" : [1311],
    "Simple_2.xes" : [332, 1329, 1823],
    "Simple_3.xes" : [678],
    "Simple_4.xes" : [532, 914, 1287],
    "Intermediate_1.xes" : [357, 956, 1458, 1865],
    "Intermediate_2.xes" : [379, 664, 966, 1369],
    "Intermediate_3.xes" : [206, 466, 1405, 1570],
    "Intermediate_4.xes" : [74, 262, 640, 841, 1112, 1245],
    "Difficult_1.xes" : [401, 1230],
    "Difficult_2.xes" : [189, 649, 854],
    "Difficult_3.xes" : [190, 800, 1153, 1783],
    "Difficult_4.xes" : [180, 712, 995],
    "BPIC2015Merged.xes" : [
        10, 20, 30, 43, 52, 64, 73, 89, 100,
        109, 119, 132, 146, 159, 177, 195,
        229, 246, 268, 282, 304, 313, 327,
        335, 351, 377, 395, 412, 460, 483,
        498, 519, 537, 563, 610, 627, 657,
        697, 716, 731, 749, 765, 780, 791,
        821, 836, 851, 868, 881, 895, 914,
        935, 954, 966, 982, 1007, 1020,
        1042, 1058, 1073, 1083, 1120, 1140,
        1155, 1166, 1188, 1201, 1213, 1245,
        1265, 1282, 1306, 1320, 1335, 1347,
        1363, 1376, 1395, 1419, 1432, 1455,
        1470, 1523, 1539, 1557, 1576, 1592,
        1607, 1624, 1637, 1658, 1690, 1710,
        1726, 1740, 1753, 1778, 1814, 1861,
        1878, 1892, 1905, 1920, 1938, 1951,
        1989, 2008, 2028, 2050, 2124, 2143,
        2157, 2179, 2193, 2215, 2230, 2245,
        2260, 2278, 2294, 2310, 2329, 2354,
        2396, 2407, 2419, 2429, 2443, 2475,
        2487, 2509, 2529, 2553, 2578, 2594,
        2612, 2655, 2667, 2687, 2715, 2735,
        2769, 2796, 2815, 2858, 2876, 2919,
        2950, 2969, 2991, 3007, 3017, 3037,
        3066, 3077, 3095, 3119, 3151, 3171,
        3191, 3201, 3212, 3229, 3237, 3256,
        3278, 3287, 3308, 3319, 3333, 3344,
        3365, 3386, 3396, 3405, 3418, 3430,
        3441, 3461, 3477, 3505, 3514, 3526,
        3553, 3567, 3597, 3621, 3639, 3655,
        3669, 3695, 3706, 3723, 3741, 3755,
        3770, 3779, 3792, 3803, 3814, 3834,
        3844, 3856, 3866, 3874, 3899, 3923,
        3934, 3947, 3956, 3966, 3983, 3993,
        4000, 4018, 4034, 4048, 4062, 4082,
        4096, 4104, 4119, 4129, 4148, 4169,
        4183, 4197, 4219, 4244, 4261, 4272,
        4305, 4317, 4326, 4348, 4362, 4371,
        4381, 4391, 4401, 4415
    ]
}

# Actual execution

EvaluatePerformance(
    methodResultsList=[
        MCDPCDDCoords,
        deSousaCoords,
        hueteCoords,
        martjushevCoords
    ],

    methodNames=[
        "MCD-PCDD",
        "de Sousa",
        "Huete",
        "Martjushev"
    ],

    allowEarlyDetection=[
        False,
        False,
        False,
        True
    ],

    actualDriftCoords=actualDriftCoords,

    lagWindow=200,

    saveFolder="Evaluation/Plots"
)