import argparse
import torch
import numpy as np
import os
import yaml

from torch.utils.data import DataLoader
from tqdm import tqdm

from collector import WindowedDataset, Collector
from sampler import Sampler
from encoder import Encoder
from comparator import Comparator
from detector import Detector

import json
import subprocess

def main(config_file, seed=1111, device='cpu'):

    # ---------------- SEEDING ----------------
    np.random.seed(seed)
    torch.manual_seed(seed)

    # ---------------- CONFIG ----------------
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    dataset_folder = config['dataset_path']
    trace_folder = config['trace_ids_path']

    # ---------------- FIND MATCHING FILES ----------------
    dataset_files = [f for f in os.listdir(dataset_folder) if f.endswith('.npy')]
    trace_files = [f for f in os.listdir(trace_folder) if f.endswith('.npy')]

    # Build mapping: prefix -> trace file
    trace_map = {}
    for tf in trace_files:
        prefix = tf.replace('_trace_ids.npy', '')
        trace_map[prefix] = tf

    # ---------------- LOOP OVER DATASETS ----------------
    evaluation_results = {}
    for df in dataset_files:

        prefix = df.replace('.npy', '')

        if prefix not in trace_map:
            print(f"Skipping {df} (no matching trace_ids)")
            continue

        print(f"\nProcessing dataset: {prefix}")

        dataset = np.load(os.path.join(dataset_folder, df), allow_pickle=True)
        dataset = torch.tensor(dataset, dtype=torch.float32)

        trace_ids = np.load(os.path.join(trace_folder, trace_map[prefix]))

        window_size = config['win_size']
        sub_window_size = int(window_size / config['sub_window_num'])
        slide = sub_window_size * config['slide_sub_windows']

        # ---------------- MODULES ----------------
        sampler = Sampler(config['m'], config['k'], device)

        model = Encoder(
            dataset.shape[1],
            config['hidden_size'],
            config['output_size']
        ).to(device)

        optimizer = torch.optim.Adam(model.parameters(), lr=config['learning_rate'])

        comparator = Comparator(
            model,
            optimizer,
            sampler,
            device,
            config['epochs'],
            config['sub_window_num'],
            config['m'],
            config['k'],
            config['eps_small'],
            config['eps_big'],
            config['temperature'],
            config['lamb'],
            config['percentile']
        )

        collector = Collector(
            window_size,
            config['sub_window_num'],
            config['min_subwindows'],
            config['max_subwindows'],
            comparator
        )

        detector = Detector(
            comparator,
            config['percentile'],
            config['consecutive_required']
        )

        # ---------------- DATA LOADER ----------------
        dataset_obj = WindowedDataset(dataset, window_size, slide)
        loader = DataLoader(dataset_obj, batch_size=1)

        # ---------------- STATE ----------------
        first = True
        threshold = 0
        drift_Trace_IDs = []

        # ---------------- MAIN LOOP ----------------
        cooldown = 0
        cooldown_windows = config['cooldown_windows']

        warmup_windows = config['warmup_windows']

        for i, window in enumerate(tqdm(loader, total=len(dataset_obj), desc=f"{prefix}")):

            if cooldown > 0:
                cooldown -= 1

            window = window.squeeze(0).to(device)

            # ---- STEP 1: SUB-WINDOWING ----
            sub_windows = collector.collect(window)

            # ---- STEP 2: ADAPTIVE SHRINK/EXPAND ----
            candidate_pool = sub_windows.copy()

            sub_windows = collector.shrink_window(sub_windows, threshold)
            sub_windows = collector.expand_window(sub_windows, candidate_pool, threshold)

            # ---- REBUILD WINDOW ----
            window = torch.cat(sub_windows, dim=0)

            # ---- STEP 3: TRAIN + UPDATE THRESHOLD ----
            retrain_interval = config['windows_per_threshold_update']

            # 🌱 WARMUP LOGIC ADDED HERE
            in_warmup = i < warmup_windows

            if (not in_warmup) and (i % retrain_interval == 0):
                threshold = comparator.train(window)
                #print("threshold:", threshold)

            # ---- STEP 4: DRIFT DETECTION ----
            if not first and cooldown == 0:

                pairwise, consecutive = comparator.test(window)

                max_disc = torch.max(consecutive)
                max_disc = torch.clamp(max_disc, 0, 50)

                # 🌱 optionally also disable detection during warmup
                if not in_warmup:

                    if max_disc > threshold:

                        if detector.detect(consecutive, threshold):

                            end_idx = min(len(dataset) - 1, i * slide + window_size)
                            drift_Trace_IDs.append(int(trace_ids[end_idx]))

                            cooldown = cooldown_windows

            first = False

        print(f"Detected drift trace IDs for {prefix}: {drift_Trace_IDs}")

        # Convert dataset filename to evaluation filename
        evaluation_results[f"{prefix}.xes"] = drift_Trace_IDs

    # ==========================================================
    # Save evaluation results
    # ==========================================================

    os.makedirs("Evaluation", exist_ok=True)

    # Keep BPIC2015 fixed because it is not rerun
    if "BPIC2015Merged.xes" not in evaluation_results:
        evaluation_results["BPIC2015Merged.xes"] = [6, 15, 28, 39, 47, 58, 67, 79, 89, 101, 110, 124, 132, 142, 151, 159, 174, 183, 192, 205, 215, 228, 237, 247, 261, 270, 301, 309, 335, 346, 362, 389, 415, 461, 491, 518, 556, 585, 608, 629, 644, 662, 679, 695, 716, 727, 746, 771, 787, 802, 824, 843, 862, 883, 906, 918, 931, 944, 960, 982, 1006, 1019, 1034, 1049, 1068, 1082, 1109, 1125, 1150, 1162, 1171, 1189, 1209, 1259, 1281, 1299, 1330, 1343, 1361, 1372, 1387, 1421, 1433, 1451, 1465, 1496, 1511, 1523, 1535, 1548, 1573, 1584, 1596, 1624, 1636, 1647, 1664, 1690, 1706, 1718, 1756, 1778, 1801, 1831, 1873, 1886, 1901, 1916, 1928, 1959, 1976, 1989, 2008, 2026, 2049, 2062, 2128, 2170, 2189, 2201, 2226, 2239, 2258, 2280, 2292, 2316, 2328, 2345, 2357, 2380, 2396, 2408, 2425, 2435, 2472, 2488, 2530, 2547, 2562, 2594, 2618, 2633, 2644, 2664, 2691, 2707, 2720, 2733, 2777, 2812, 2825, 2835, 2845, 2879, 2901, 2919, 2930, 2955, 2988, 3007, 3022, 3035, 3070, 3082, 3103, 3114, 3131, 3168, 3179, 3229, 3237, 3256, 3276, 3314, 3328, 3340, 3351, 3373, 3383, 3405, 3420, 3436, 3459, 3504, 3512, 3552, 3567, 3585, 3600, 3613, 3624, 3655, 3688, 3698, 3720, 3744, 3780, 3804, 3814, 3834, 3851, 3868, 3883, 3897, 3906, 3920, 3947, 3960, 3979, 3990, 3999, 4011, 4036, 4049, 4059, 4074, 4092, 4102, 4120, 4146, 4155, 4172, 4185, 4197, 4206, 4216, 4240, 4259, 4272, 4314, 4323, 4333, 4346, 4357, 4370, 4387, 4398, 4407]

    with open("Evaluation/ParamSensResults.json", "w") as f:
        json.dump(evaluation_results, f, indent=4)

    print("\nSaved evaluation results to Evaluation/ParamSensResults.json")

    # ==========================================================
    # Automatically run evaluation
    # ==========================================================

    print("\nLaunching evaluation...\n")

    subprocess.run(
        ["python", "Evaluation/EvaluatePerformance.py"],
        check=True
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_file", required=True)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    main(args.config_file, device=device)