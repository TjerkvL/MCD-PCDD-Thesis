#Imports
import numpy as np
import matplotlib.pyplot as plt

import json

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
    "BPIC2015Merged.xes" : [1079, 1948, 3299, 4388]
}


def EvaluatePerformance(method_results_list, method_names, actualDriftCoords, lag_window=50, 
                        plot=True, save_folder="evaluation_plots"):

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
    # Consistent colors
    # ============================================================

    cmap = plt.get_cmap("tab10")

    method_colors = {
        method_names[i]: cmap(i % 10)
        for i in range(len(method_names))
    }

    # ============================================================
    # Storage
    # ============================================================

    all_results = {}

    overall_f1_scores = []
    overall_precisions = []
    overall_recalls = []
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

        precision_scores = [
            results[log]["Precision"]
            for log in matching_logs
        ]

        recall_scores = [
            results[log]["Recall"]
            for log in matching_logs
        ]

        latencies = [
            results[log]["Avg Latency"]
            for log in matching_logs
            if results[log]["Avg Latency"] is not None
        ]

        return {
            "Average F1-score": np.mean(f1_scores),
            "Average Precision": np.mean(precision_scores),
            "Average Recall": np.mean(recall_scores),
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
        all_precisions = []
        all_recalls = []
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
            # Match detections
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
            all_precisions.append(precision)
            all_recalls.append(recall)

            if latencies:
                all_latencies.extend(latencies)

            # ----------------------------------------------------
            # Print results
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
        overall_precision = np.mean(all_precisions)
        overall_recall = np.mean(all_recalls)

        overall_latency = (
            np.mean(all_latencies)
            if all_latencies else None
        )

        results["OVERALL"] = {
            "Average F1-score": overall_f1,
            "Average Precision": overall_precision,
            "Average Recall": overall_recall,
            "Average Latency": overall_latency
        }

        # --------------------------------------------------------
        # Category averages
        # --------------------------------------------------------

        results["SIMPLE_AVERAGE"] = compute_group_average(results, "Simple")
        results["INTERMEDIATE_AVERAGE"] = compute_group_average(results, "Intermediate")
        results["DIFFICULT_AVERAGE"] = compute_group_average(results, "Difficult")

        # --------------------------------------------------------
        # Print summaries
        # --------------------------------------------------------

        print("\n--- CATEGORY AVERAGES ---")

        for category in [
            "SIMPLE_AVERAGE",
            "INTERMEDIATE_AVERAGE",
            "DIFFICULT_AVERAGE"
        ]:

            category_results = results[category]

            print(f"\n{category}")

            print(f"Average F1-score  : {category_results['Average F1-score']:.4f}")
            print(f"Average Precision : {category_results['Average Precision']:.4f}")
            print(f"Average Recall    : {category_results['Average Recall']:.4f}")

            latency = category_results["Average Latency"]

            if latency is not None:
                print(f"Average Latency  : {latency:.2f}")
            else:
                print("Average Latency  : None")

        print("\n--- OVERALL ---")
        print(f"Average F1-score  : {overall_f1:.4f}")
        print(f"Average Precision : {overall_precision:.4f}")
        print(f"Average Recall    : {overall_recall:.4f}")

        if overall_latency is not None:
            print(f"Average Latency  : {overall_latency:.2f}")
        else:
            print("Average Latency  : None")

        # --------------------------------------------------------
        # Save results
        # --------------------------------------------------------

        all_results[method_name] = results

        overall_f1_scores.append(overall_f1)
        overall_precisions.append(overall_precision)
        overall_recalls.append(overall_recall)

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
        # Shared bar colors
        # --------------------------------------------------------

        bar_colors = [method_colors[m] for m in method_names]

        # --------------------------------------------------------
        # Average F1
        # --------------------------------------------------------

        plt.figure(figsize=(10, 6))

        plt.bar(
            method_names,
            overall_f1_scores,
            color=bar_colors,
            width=0.5
        )

        plt.ylim(0, 0.6)

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
        # Average Precision
        # --------------------------------------------------------

        plt.figure(figsize=(10, 6))

        plt.bar(
            method_names,
            overall_precisions,
            color=bar_colors,
            width=0.5
        )

        plt.ylim(0, 0.6)

        plt.title("Average Precision per Method")
        plt.ylabel("Average Precision")
        plt.xticks(rotation=15)

        plt.tight_layout()

        plt.savefig(
            os.path.join(save_folder, "average_precision_scores.png"),
            dpi=300,
            bbox_inches='tight'
        )

        plt.close()

        # --------------------------------------------------------
        # Average Recall
        # --------------------------------------------------------

        plt.figure(figsize=(10, 6))

        plt.bar(
            method_names,
            overall_recalls,
            color=bar_colors,
            width=0.5
        )


        plt.ylim(0, 0.6)

        plt.title("Average Recall per Method")
        plt.ylabel("Average Recall")
        plt.xticks(rotation=15)

        plt.tight_layout()

        plt.savefig(
            os.path.join(save_folder, "average_recall_scores.png"),
            dpi=300,
            bbox_inches='tight'
        )

        plt.close()

        # --------------------------------------------------------
        # Average Latency
        # --------------------------------------------------------

        plt.figure(figsize=(10, 6))

        plt.bar(
            method_names,
            overall_latencies,
            color=bar_colors,
            width=0.5
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
    "Difficult_4.xes" : [375, 609, 792]
}

MCDPCDDCoords = {
    "Simple_1.xes" : [304, 539],
    "Simple_2.xes" : [925],
    "Simple_3.xes" : [263, 733, 1176],
    "Simple_4.xes" : [560, 1116],
    "Intermediate_1.xes" : [600, 1330, 1988],
    "Intermediate_2.xes" : [873, 1566, 1899],
    "Intermediate_3.xes" : [92, 295, 570, 830, 997, 1298, 1582, 1733, 1894],
    "Intermediate_4.xes" : [150, 345, 650, 800, 1064, 1177, 1338, 1437, 1639, 1760],
    "Difficult_1.xes" : [908, 1230],
    "Difficult_2.xes" : [82, 189, 354, 515, 616, 822],
    "Difficult_3.xes" : [175, 473, 1041, 1286, 1678],
    "Difficult_4.xes" : [850],
    "BPIC2015Merged.xes" : [10, 20, 30, 43, 52, 64, 73, 89, 100, 109, 119, 132, 146, 159, 177, 195, 229, 246, 268, 282, 304, 313, 327, 335, 351, 377, 395, 412, 460, 483, 498, 519, 537, 563, 610, 627, 657, 697, 716, 731, 749, 765, 780, 791, 821, 836, 851, 868, 881, 895, 914, 935, 954, 966, 982, 1007, 1020, 1042, 1058, 1073, 1083, 1120, 1140, 1155, 1166, 1188, 1201, 1213, 1245, 1265, 1282, 1306, 1320, 1335, 1347, 1363, 1376, 1395, 1419, 1432, 1455, 1470, 1523, 1539, 1557, 1576, 1592, 1607, 1624, 1637, 1658, 1690, 1710, 1726, 1740, 1753, 1778, 1814, 1861, 1878, 1892, 1905, 1920, 1938, 1951, 1989, 2008, 2028, 2050, 2124, 2143, 2157, 2179, 2193, 2215, 2230, 2245, 2260, 2278, 2294, 2310, 2329, 2354, 2396, 2407, 2419, 2429, 2443, 2475, 2487, 2509, 2529, 2553, 2578, 2594, 2612, 2655, 2667, 2687, 2715, 2735, 2769, 2796, 2815, 2858, 2876, 2919, 2950, 2969, 2991, 3007, 3017, 3037, 3066, 3077, 3095, 3119, 3151, 3171, 3191, 3201, 3212, 3229, 3237, 3256, 3278, 3287, 3308, 3319, 3333, 3344, 3365, 3386, 3396, 3405, 3418, 3430, 3441, 3461, 3477, 3505, 3514, 3526, 3553, 3567, 3597, 3621, 3639, 3655, 3669, 3695, 3706, 3723, 3741, 3755, 3770, 3779, 3792, 3803, 3814, 3834, 3844, 3856, 3866, 3874, 3899, 3923, 3934, 3947, 3956, 3966, 3983, 3993, 4000, 4018, 4034, 4048, 4062, 4082, 4096, 4104, 4119, 4129, 4148, 4169, 4183, 4197, 4219, 4244, 4261, 4272, 4305, 4317, 4326, 4348, 4362, 4371, 4381, 4391, 4401, 4415]
}

with open("Evaluation/ParamSensResults.json", "r") as f:
    ParamSens = json.load(f)


EvaluatePerformance(
        method_results_list=[
        deSousaCoords,
        hueteCoords,
        martjushevCoords,
        ParamSens],
    method_names=[
        "de Sousa",
        "Huete",
        "Martjushev",
        "MCDPCDD"],
    actualDriftCoords=actualDriftCoords,
    lag_window=200,
    save_folder="Evaluation/Plots"
)