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
    "BPIC2015Merged.xes" : [1199, 2031, 3440, 4493]
}


def EvaluatePerformance(method_results_list, method_names, actualDriftCoords, lag_window=50, 
                        plot=True, save_folder="evaluation_plots"):
    """
    Evaluates multiple concept drift detection methods.

    Parameters
    ----------
    method_results_list : list[dict]
        List of dictionaries containing detected drift coordinates per method.

    method_names : list[str]
        Names corresponding to the dictionaries in method_results_list.

    actualDriftCoords : dict
        Dictionary containing actual drift locations.

    lag_window : int
        Maximum allowed detection delay to count as TP.

    plot : bool
        Whether to generate and save plots.

    save_folder : str
        Folder where plots will be stored.

    Returns
    -------
    all_results : dict
        Nested dictionary containing all evaluation results.
    """

    import os
    import numpy as np
    import matplotlib.pyplot as plt

    # ============================================================
    # Validation
    # ============================================================

    if len(method_results_list) != len(method_names):
        raise ValueError("method_results_list and method_names must have equal length.")

    os.makedirs(save_folder, exist_ok=True)

    # ============================================================
    # Metadata used for plots
    # ============================================================

    noise_levels = {
        "Simple_1.xes": 0.0, "Simple_2.xes": 0.0,
        "Simple_3.xes": 0.0, "Simple_4.xes": 0.0,

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

    # ============================================================
    # Consistent colors for all methods
    # ============================================================

    cmap = plt.get_cmap("tab10")
    method_colors = {
        method_names[i]: cmap(i % 10)
        for i in range(len(method_names))
    }

    # ============================================================
    # Store everything here
    # ============================================================

    all_results = {}

    overall_f1_scores = []
    overall_latencies = []

    # ============================================================
    # Helper functions
    # ============================================================

    def aggregate_metric(results, metric_key, mapping):
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

    def compute_group_average(results, group_prefix):
        matching_logs = [
            log for log in results.keys()
            if log.startswith(group_prefix)
        ]

        if len(matching_logs) == 0:
            return None

        f1_scores = [results[log]["F1-score"] for log in matching_logs]
        latencies = [
            results[log]["Avg Latency"]
            for log in matching_logs
            if results[log]["Avg Latency"] is not None
        ]

        return {
            "Average F1-score": np.mean(f1_scores),
            "Average Latency": np.mean(latencies) if latencies else None
        }

    # ============================================================
    # Evaluate every method
    # ============================================================

    for method_idx, detectedDriftCoords in enumerate(method_results_list):

        method_name = method_names[method_idx]

        print("\n" + "=" * 80)
        print(f"METHOD: {method_name}")
        print("=" * 80)

        results = {}

        all_f1 = []
        all_latencies = []

        # --------------------------------------------------------
        # Evaluate every log
        # --------------------------------------------------------

        for log_name in actualDriftCoords:

            actual = sorted(actualDriftCoords[log_name])
            detected = sorted(detectedDriftCoords.get(log_name, []))

            matched_actual = set()
            matched_detected = set()

            latencies = []

            # ----------------------------------------------------
            # Match detections to actual drifts
            # ----------------------------------------------------

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

            # ----------------------------------------------------
            # Metrics
            # ----------------------------------------------------

            TP = len(matched_actual)
            FP = len(detected) - TP
            FN = len(actual) - TP

            precision = TP / (TP + FP) if (TP + FP) > 0 else 0
            recall = TP / (TP + FN) if (TP + FN) > 0 else 0

            f1 = (
                2 * precision * recall / (precision + recall)
                if (precision + recall) > 0 else 0
            )

            avg_latency = np.mean(latencies) if latencies else None

            # ----------------------------------------------------
            # Store results
            # ----------------------------------------------------

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

            # ----------------------------------------------------
            # Print log results
            # ----------------------------------------------------

            print(f"\n{log_name}")
            print("-" * 40)
            print(f"F1-score     : {f1:.4f}")
            print(f"Precision    : {precision:.4f}")
            print(f"Recall       : {recall:.4f}")
            print(f"TP / FP / FN : {TP} / {FP} / {FN}")

            if avg_latency is not None:
                print(f"Avg Latency  : {avg_latency:.2f}")
            else:
                print("Avg Latency  : None")

        # --------------------------------------------------------
        # Overall metrics
        # --------------------------------------------------------

        overall_f1 = np.mean(all_f1)
        overall_latency = np.mean(all_latencies) if all_latencies else None

        results["OVERALL"] = {
            "Average F1-score": overall_f1,
            "Average Latency": overall_latency
        }

        # --------------------------------------------------------
        # Category averages
        # --------------------------------------------------------

        results["SIMPLE_AVERAGE"] = compute_group_average(results, "Simple")
        results["INTERMEDIATE_AVERAGE"] = compute_group_average(results, "Intermediate")
        results["DIFFICULT_AVERAGE"] = compute_group_average(results, "Difficult")

        # --------------------------------------------------------
        # Print category summaries
        # --------------------------------------------------------

        print("\n--- CATEGORY AVERAGES ---")

        for category in [
            "SIMPLE_AVERAGE",
            "INTERMEDIATE_AVERAGE",
            "DIFFICULT_AVERAGE"
        ]:

            category_results = results[category]

            print(f"\n{category}")

            print(
                f"Average F1-score : "
                f"{category_results['Average F1-score']:.4f}"
            )

            latency = category_results["Average Latency"]

            if latency is not None:
                print(f"Average Latency : {latency:.2f}")
            else:
                print("Average Latency : None")

        print("\n--- OVERALL ---")
        print(f"Average F1-score : {overall_f1:.4f}")

        if overall_latency is not None:
            print(f"Average Latency : {overall_latency:.2f}")
        else:
            print("Average Latency : None")

        # --------------------------------------------------------
        # Save method results
        # --------------------------------------------------------

        all_results[method_name] = results

        overall_f1_scores.append(overall_f1)
        overall_latencies.append(
            overall_latency if overall_latency is not None else 0
        )

    # ============================================================
    # PLOTS
    # ============================================================

    if plot:

        # --------------------------------------------------------
        # Combined line charts
        # --------------------------------------------------------

        fig, axs = plt.subplots(2, 2, figsize=(14, 10))

        # ========================================================
        # Plot each method
        # ========================================================

        for method_name in method_names:

            results = all_results[method_name]

            color = method_colors[method_name]

            # Noise vs F1
            noise_x_acc, noise_y_acc = aggregate_metric(
                results, "F1-score", noise_levels
            )

            axs[0, 0].plot(
                noise_x_acc,
                noise_y_acc,
                marker='o',
                label=method_name,
                color=color
            )

            # Drift spacing vs F1
            freq_x_acc, freq_y_acc = aggregate_metric(
                results, "F1-score", drift_spacing
            )

            axs[0, 1].plot(
                freq_x_acc,
                freq_y_acc,
                marker='o',
                label=method_name,
                color=color
            )

            # Noise vs latency
            noise_x_lat, noise_y_lat = aggregate_metric(
                results, "Avg Latency", noise_levels
            )

            axs[1, 0].plot(
                noise_x_lat,
                noise_y_lat,
                marker='o',
                label=method_name,
                color=color
            )

            # Drift spacing vs latency
            freq_x_lat, freq_y_lat = aggregate_metric(
                results, "Avg Latency", drift_spacing
            )

            axs[1, 1].plot(
                freq_x_lat,
                freq_y_lat,
                marker='o',
                label=method_name,
                color=color
            )

        # ========================================================
        # Titles and labels
        # ========================================================

        axs[0, 0].set_title("Noise vs F1-score")
        axs[0, 0].set_xlabel("Noise Level")
        axs[0, 0].set_ylabel("F1-score")
        axs[0, 0].legend()

        axs[0, 1].set_title("Drift Spacing vs F1-score")
        axs[0, 1].set_xlabel("Drift Spacing")
        axs[0, 1].set_ylabel("F1-score")
        axs[0, 1].legend()

        axs[1, 0].set_title("Noise vs Latency")
        axs[1, 0].set_xlabel("Noise Level")
        axs[1, 0].set_ylabel("Latency")
        axs[1, 0].legend()

        axs[1, 1].set_title("Drift Spacing vs Latency")
        axs[1, 1].set_xlabel("Drift Spacing")
        axs[1, 1].set_ylabel("Latency")
        axs[1, 1].legend()

        plt.tight_layout()

        plt.savefig(
            os.path.join(save_folder, "combined_line_charts.png"),
            dpi=300,
            bbox_inches='tight'
        )

        plt.close()

        # --------------------------------------------------------
        # Bar chart - Average F1
        # --------------------------------------------------------

        plt.figure(figsize=(10, 6))

        bar_colors = [method_colors[m] for m in method_names]

        plt.bar(
            method_names,
            overall_f1_scores,
            color=bar_colors
        )

        plt.title("Average F1-score per Method")
        plt.ylabel("Average F1-score")
        plt.xticks(rotation=15)

        plt.tight_layout()

        plt.savefig(
            os.path.join(save_folder, "average_f1_scores.png"),
            dpi=300,
            bbox_inches='tight'
        )

        plt.close()

        # --------------------------------------------------------
        # Bar chart - Average Latency
        # --------------------------------------------------------

        plt.figure(figsize=(10, 6))

        plt.bar(
            method_names,
            overall_latencies,
            color=bar_colors
        )

        plt.title("Average Latency per Method")
        plt.ylabel("Latency")
        plt.xticks(rotation=15)

        plt.tight_layout()

        plt.savefig(
            os.path.join(save_folder, "average_latencies.png"),
            dpi=300,
            bbox_inches='tight'
        )

        plt.close()

        print("\nPlots saved to:")
        print(save_folder)

    return all_results


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

MCDPCDD = {
    "Simple_1.xes" : [],
    "Simple_2.xes" : [1007, 1408],
    "Simple_3.xes" : [],
    "Simple_4.xes" : [649],
    "Intermediate_1.xes" : [382, 1458],
    "Intermediate_2.xes" : [322, 640, 986, 1247, 1577, 1869],
    "Intermediate_3.xes" : [1323, 1486],
    "Intermediate_4.xes" : [108, 640, 841, 1139, 1344, 1489, 1591, 1699, 1943],
    "Difficult_1.xes" : [189, 426, 846, 1292, 1597],
    "Difficult_2.xes" : [189, 854],
    "Difficult_3.xes" : [780, 1427],
    "Difficult_4.xes" : [712],
    "BPIC2015Merged.xes" : [1199, 2031, 3440, 4493, 5649]
}

EvaluatePerformance(MCDPCDD, actualDriftCoords, lag_window=150)
