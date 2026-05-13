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

            if i % retrain_interval == 0:
                threshold = comparator.train(window)

            # ---- STEP 4: DRIFT DETECTION ----
            if not first and cooldown == 0:

                pairwise, consecutive = comparator.test(window)

                max_disc = torch.max(consecutive)

                if max_disc > threshold:

                    if detector.detect(consecutive, threshold):

                        end_idx = min(len(dataset) - 1, i * slide + window_size)
                        drift_Trace_IDs.append(int(trace_ids[end_idx]))

                        cooldown = cooldown_windows

            first = False

        print(f"Detected drift trace IDs for {prefix}: {drift_Trace_IDs}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_file", required=True)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    main(args.config_file, device=device)