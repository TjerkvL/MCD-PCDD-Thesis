import argparse
import torch
import numpy as np
import os
import yaml

from torch.utils.data import DataLoader

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

    # ---------------- DATA ----------------
    dataset = np.load(config['dataset_path'], allow_pickle=True)
    dataset = torch.tensor(dataset, dtype=torch.float32)

    trace_ids = np.load(config['trace_ids_path'])

    window_size = config['win_size']
    slide = int(window_size / config['sub_window_num'])

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
    loader = DataLoader(
        WindowedDataset(dataset, window_size, slide),
        batch_size=1
    )

    # ---------------- STATE ----------------
    first = True
    threshold = 0

    # ---------------- MAIN LOOP ----------------
    for i, window in enumerate(loader):

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
        threshold = comparator.train(window)

        # ---- STEP 4: DRIFT DETECTION ----
        if not first:

            # FULL MCD STRUCTURE (pairwise + consecutive)
            pairwise, consecutive = comparator.test(window)

            # GLOBAL MAXIMUM CONCEPT DISCREPANCY
            max_disc = torch.max(pairwise)

            if max_disc > threshold:

                # CONSECUTIVE DRIFT CHECK
                if detector.detect(consecutive, threshold):

                    start_idx = max(0, i * slide + window_size - slide)
                    end_idx = min(len(dataset), i * slide + window_size)

                    print(f"Drift detected at trace {trace_ids[end_idx]}")

        first = False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_file", required=True)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    main(args.config_file, device=device)