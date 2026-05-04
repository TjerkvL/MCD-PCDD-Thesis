import argparse
from logging import config
import yaml
import torch
import numpy as np
import os

from torch.utils.data import DataLoader

from collector import WindowedDataset, Collector
from sampler import Sampler
from encoder import Encoder
from comparator import Comparator
from detector import Detector


def main(config_file, seed=1111, device='cpu'):

    np.random.seed(seed)
    torch.manual_seed(seed)

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    dataset = np.load(config['dataset_path'], allow_pickle=True)
    dataset = torch.tensor(dataset, dtype=torch.float32)
    
    if not os.path.exists(config['trace_ids_path']):
        raise FileNotFoundError(f"Cannot find trace_ids at {config['trace_ids_path']}")
    trace_ids = np.load(config['trace_ids_path'])

    window_size = config['win_size']
    slide = int(window_size / config['sub_window_num'])

    sampler = Sampler(config['m'], config['k'], device)

    model = Encoder(
        dataset.shape[1],
        config['hidden_size'],
        config['output_size']
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=config['learning_rate'])

    comparator = Comparator(
        model, optimizer, sampler, device,
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

    loader = DataLoader(
        WindowedDataset(dataset, window_size, slide),
        batch_size=1
    )  

    first = True
    threshold = 0

    for i, window in enumerate(loader):

        window = window.squeeze(0).to(device)

        # --- STEP 1: create initial subwindows ---
        sub_windows = collector.collect(window)

        # --- STEP 2: adaptive logic ---
        candidate_pool = sub_windows.copy()

        sub_windows = collector.shrink_window(sub_windows, threshold)
        sub_windows = collector.expand_window(sub_windows, candidate_pool, threshold)

        # --- IMPORTANT: rebuild window ---
        window = torch.cat(sub_windows, dim=0)

        # --- STEP 3: MCD ---
        if not first:
            distances = comparator.test(window)

            if distances[-1] > threshold:
                start_idx = max(0, i * slide + window_size - slide)
                end_idx = min(len(dataset), i * slide + window_size)

                if detector.detect(distances, threshold):
                    print(f"Drift at trace {trace_ids[start_idx]}")

        threshold = comparator.train(window)
        first = False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_file", required=True)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    main(args.config_file, device=device)