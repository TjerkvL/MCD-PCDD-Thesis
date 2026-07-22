# Imports
import argparse
import os
import yaml

import numpy as np
import torch

from torch.utils.data import DataLoader
from tqdm import tqdm

#Import all components
from collector import WindowedDataset, Collector
from sampler import Sampler
from encoder import Encoder
from comparator import Comparator
from detector import Detector

"""
    INPUT:
        event log               (.npy file #1 created by xesToNpy.py)
        event log trace IDs     (.npy #2 file created by xesToNpy.py)
        configuration file      (.yaml file)

    OUTPUT:
        detected drift trace IDs
"""


def main(configFile, seed=1111, device='cpu'):

    # Seed initialization
    np.random.seed(seed)
    torch.manual_seed(seed)

    # Load configuration
    with open(configFile, 'r') as file:
        config = yaml.safe_load(file)

    datasetFolder = config['dataset_path']
    traceFolder = config['trace_ids_path']

    # Find matching dataset and trace files
    datasetFiles = [file for file in os.listdir(datasetFolder) if file.endswith('.npy')]
    traceFiles = [file for file in os.listdir(traceFolder) if file.endswith('.npy')]

    # Create trace file mapping
    traceMap = {}

    for traceFile in traceFiles:
        prefix = traceFile.replace('_trace_ids.npy', '')
        traceMap[prefix] = traceFile

    # Process every dataset
    for datasetFile in datasetFiles:

        prefix = datasetFile.replace('.npy', '')

        if prefix not in traceMap:
            print(f"Skipping {datasetFile} (no matching trace_ids)")
            continue

        print(f"\nProcessing dataset: {prefix}")

        dataset = np.load(os.path.join(datasetFolder, datasetFile), allow_pickle=True)
        dataset = torch.tensor(dataset, dtype=torch.float32)

        traceIDs = np.load(os.path.join(traceFolder, traceMap[prefix]))

        windowSize = config['win_size']
        subWindowSize = int(windowSize / config['sub_window_num'])
        slide = subWindowSize * config['slide_sub_windows']

        # Create modules
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
            windowSize,
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

        # Create data loader
        datasetObject = WindowedDataset(dataset, windowSize, slide)
        loader = DataLoader(datasetObject, batch_size=1)

        # Detection state
        firstWindow = True
        threshold = 0
        driftTraceIDs = []

        cooldown = 0
        cooldownWindows = config['cooldown_windows']
        warmupWindows = config['warmup_windows']

        # Main detection loop
        for i, window in enumerate(
            tqdm(loader, total=len(datasetObject), desc=f"{prefix}")
        ):

            if cooldown > 0:
                cooldown -= 1

            window = window.squeeze(0).to(device)

            # Split into sub-windows
            subWindows = collector.collect(window)

            # Adaptive shrink/expand
            candidatePool = subWindows.copy()
            subWindows = collector.shrinkWindow(subWindows, threshold)
            subWindows = collector.expandWindow(subWindows, candidatePool, threshold)

            # Rebuild window
            window = torch.cat(subWindows, dim=0)

            # Train and update threshold
            retrainInterval = config['windows_per_threshold_update']
            inWarmup = i < warmupWindows

            if not inWarmup and i % retrainInterval == 0:
                threshold = comparator.train(window)

            # Drift detection
            if not firstWindow and cooldown == 0:

                pairwise, consecutive = comparator.test(window)

                maximumDiscrepancy = torch.max(consecutive)
                maximumDiscrepancy = torch.clamp(maximumDiscrepancy, 0, 50)

                if not inWarmup:

                    if maximumDiscrepancy > threshold:

                        if detector.detect(consecutive, threshold):

                            endIndex = min(len(dataset) - 1, i * slide + windowSize)

                            driftTraceIDs.append(int(traceIDs[endIndex]))

                            cooldown = cooldownWindows

            firstWindow = False

        print(f"Detected drift trace IDs for {prefix}: {driftTraceIDs}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--config_file", required=True)

    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("Using device:", device)

    main(args.config_file, device=device)