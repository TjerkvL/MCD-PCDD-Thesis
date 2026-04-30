#Imports
import numpy as np
import matplotlib.pyplot as plt

#Actual drift locations, coupling the file name with the trace numbers
actualDriftCoords = {
    "Simple_1.xes" : [1000],
    "Simple_2.xes" : [666],
    "Simple_3.xes" : [666, 1333],
    "Simple_4.xes" : [500, 1500],
    "Intermediate_1.xes" : [666, 1333],
    "Intermediate_2.xes" : [800, 1200],
    "Intermediate_3.xes" : [666, 1333],
    "Intermediate_4.xes" : [800, 1200],
    "Difficult_1.xes" : [400, 800, 1200],
    "Difficult_2.xes" : [400, 600, 800],
    "Difficult_3.xes" : [400, 800, 1200],
    "Difficult_4.xes" : [400, 600, 800],
    "BPIC2015Merged.xes" : [1199, 2031, 3440, 4493, 5649]
}


def EvaluatePerformance(detectedDriftCoords, actualDriftCoords, lag_window=50, plot=True):
    """ Functiont that takes as input the detected drift locations and outputs most relevant performance metrics """
    

    #Intialize lists to be filled with the results
    results = {}
    all_f1 = []
    all_latencies = []

    # Calculate for each event log the performance and add the results to the earlier created lists
    for log_name in actualDriftCoords:
        actual = sorted(actualDriftCoords[log_name])
        detected = sorted(detectedDriftCoords.get(log_name, []))

        matched_actual = set()
        matched_detected = set()
        latencies = []

        for i, a in enumerate(actual):
            best_distance = float('inf')
            best_j = None

            for j, d in enumerate(detected):
                if j in matched_detected:
                    continue

                distance = d - a
                if 0 <= distance <= lag_window and distance < best_distance:
                    best_distance = distance
                    best_j = j

            if best_j is not None:
                matched_actual.add(i)
                matched_detected.add(best_j)
                latencies.append(best_distance)

        TP = len(matched_actual)
        FP = len(detected) - TP
        FN = len(actual) - TP

        precision = TP / (TP + FP) if (TP + FP) > 0 else 0
        recall = TP / (TP + FN) if (TP + FN) > 0 else 0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0

        avg_latency = np.mean(latencies) if latencies else None

        results[log_name] = {
            "F1-score": f1,
            "Precision": precision,
            "Recall": recall,
            "TP": TP,
            "FP": FP,
            "FN": FN,
            "Avg Latency": avg_latency
        }

        all_f1.append(f1)
        if latencies:
            all_latencies.extend(latencies)

        print(f"{log_name}:")
        print(f"  F1-score: {f1:.4f}")
        print(f"  Precision: {precision:.4f}, Recall: {recall:.4f}")
        print(f"  TP: {TP}, FP: {FP}, FN: {FN}")
        print(f"  Avg Latency: {avg_latency:.2f}" if avg_latency is not None else "  Avg Latency: None")
        print()

    overall_f1 = np.mean(all_f1)
    overall_latency = np.mean(all_latencies) if all_latencies else None

    print("=== Average Evaluation Results ===")
    print(f"Average F1-score: {overall_f1:.4f}")
    print(f"Average Latency: {overall_latency:.2f}" if overall_latency is not None else "Average Latency: None")

    results["OVERALL"] = {
        "Average F1-score": overall_f1,
        "Average Latency": overall_latency
    }

    #Creation of the plots showing the effect of noise drift frequency on accuracy and latency
    noise_levels = {
        "Simple_1.xes": 0.0, "Simple_2.xes": 0.0, "Simple_3.xes": 0.0, "Simple_4.xes": 0.0,
        "Intermediate_1.xes": 0.1, "Intermediate_3.xes": 0.1,
        "Intermediate_2.xes": 0.2, "Intermediate_4.xes": 0.2,
        "Difficult_1.xes": 0.2, "Difficult_3.xes": 0.2,
        "Difficult_2.xes": 0.35, "Difficult_4.xes": 0.35,
    }

    drift_spacing = {
        "Intermediate_1.xes": 667, "Intermediate_3.xes": 667,
        "Intermediate_2.xes": 400, "Intermediate_4.xes": 400,
        "Difficult_1.xes": 400, "Difficult_3.xes": 400,
        "Difficult_2.xes": 200, "Difficult_4.xes": 200,
    }

    def aggregate(metric_key, mapping):
        grouped = {}
        for log, value in mapping.items():
            if log not in results:
                continue
            metric = results[log][metric_key]
            if metric is None:
                continue

            grouped.setdefault(value, []).append(metric)

        x = sorted(grouped.keys())
        y = [np.mean(grouped[v]) for v in x]
        return x, y

    if plot:
        noise_x_acc, noise_y_acc = aggregate("F1-score", noise_levels)
        noise_x_lat, noise_y_lat = aggregate("Avg Latency", noise_levels)

        freq_x_acc, freq_y_acc = aggregate("F1-score", drift_spacing)
        freq_x_lat, freq_y_lat = aggregate("Avg Latency", drift_spacing)

        fig, axs = plt.subplots(2, 2, figsize=(12, 10))

        # Top-left: Noise vs Accuracy
        axs[0, 0].plot(noise_x_acc, noise_y_acc, marker='o')
        axs[0, 0].set_title("Noise vs F1-score")
        axs[0, 0].set_xlabel("Noise Level")
        axs[0, 0].set_ylabel("F1-score")

        # Top-right: Drift Frequency vs Accuracy
        axs[0, 1].plot(freq_x_acc, freq_y_acc, marker='o')
        axs[0, 1].set_title("Drift Spacing vs F1-score")
        axs[0, 1].set_xlabel("Drift Spacing")
        axs[0, 1].set_ylabel("F1-score")

        # Bottom-left: Noise vs Latency
        axs[1, 0].plot(noise_x_lat, noise_y_lat, marker='o')
        axs[1, 0].set_title("Noise vs Latency")
        axs[1, 0].set_xlabel("Noise Level")
        axs[1, 0].set_ylabel("Latency")

        # Bottom-right: Drift Frequency vs Latency
        axs[1, 1].plot(freq_x_lat, freq_y_lat, marker='o')
        axs[1, 1].set_title("Drift Spacing vs Latency")
        axs[1, 1].set_xlabel("Drift Spacing")
        axs[1, 1].set_ylabel("Latency")

        plt.tight_layout()
        plt.show()

    return results


#Dictionary of the resuls to be evaluated, coupling the file name with the list of detected drift locations
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
    "BPIC2015Merged.xes" : [396, 1047, 1226, 1465, 2037, 2457, 2960, 3446, 3677, 4195, 4413]
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
    "BPIC2015Merged.xes" : [901, 1089, 1170, 1191, 1207, 1224, 1260, 1460, 1508, 1553, 1599, 1624, 1659, 1837, 1863, 1948, 2188, 2227, 2260, 2329, 2495, 2511, 4549, 5636]
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
    "Difficult_4.xes" : [375, 609, 792],
    "BPIC2015Merged.xes" : [1199, 2031, 3440, 4493, 5649]
}

EvaluatePerformance(hueteCoords, actualDriftCoords, lag_window=150)
