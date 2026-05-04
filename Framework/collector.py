import torch
from torch.utils.data import Dataset


class WindowedDataset(Dataset):
    """
    INPUT:
        dataset: torch.Tensor [T, F]
    OUTPUT:
        window: torch.Tensor [window_size, F]
    """

    def __init__(self, dataset, window_size, slide):
        self.dataset = dataset
        self.window_size = window_size
        self.slide = slide

    def __len__(self):
        return max(1, (len(self.dataset) - self.window_size) // self.slide + 1)

    def __getitem__(self, idx):
        start = idx * self.slide
        end = start + self.window_size
        return self.dataset[start:end]


class Collector:
    """
    INPUT:
        window_data: torch.Tensor [T_window, F]
    OUTPUT:
        list[torch.Tensor] sub_windows
    """

    def __init__(self, window_size, sub_window_num, min_subwindows, max_subwindows, comparator):
        self.window_size = window_size
        self.sub_window_num = sub_window_num
        self.min_subwindows = min_subwindows
        self.max_subwindows = max_subwindows
        self.comparator = comparator

    # ---------- BASIC SPLIT ----------
    def collect(self, window_data):
        sub_size = int(window_data.size(0) / self.sub_window_num)
        return list(torch.split(window_data, sub_size))

    # ---------- INTERNAL EMBEDDING ----------
    def _embed(self, sub_window):
        samples = self.comparator.generate_samples(sub_window)
        embeddings = self.comparator.model(samples).mean(dim=1)
        return embeddings

    # ---------- PAIRWISE DISCREPANCY ----------
    def compute_pairwise_discrepancy(self, sub_windows):
        discrepancies = []

        for i in range(len(sub_windows)):
            for j in range(i + 1, len(sub_windows)):
                emb_i = self._embed(sub_windows[i])
                emb_j = self._embed(sub_windows[j])

                dist = self.comparator.compute_negative_loss(emb_i, emb_j)
                discrepancies.append(dist)

        return torch.stack(discrepancies)

    # ---------- SHRINK ----------
    def shrink_window(self, sub_windows, threshold):
        while len(sub_windows) > self.min_subwindows:
            discrepancies = self.compute_pairwise_discrepancy(sub_windows)
            max_disc = torch.max(discrepancies)

            if max_disc <= threshold:
                break

            sub_windows = sub_windows[1:]

        return sub_windows

    # ---------- EXPAND ----------
    def expand_window(self, sub_windows, candidate_pool, threshold):
        while len(sub_windows) < self.max_subwindows and len(candidate_pool) > 0:

            new_sub_windows = [candidate_pool[-1]] + sub_windows

            discrepancies = self.compute_pairwise_discrepancy(new_sub_windows)
            max_disc = torch.max(discrepancies)

            if max_disc > threshold:
                break

            sub_windows = new_sub_windows
            candidate_pool = candidate_pool[:-1]

        return sub_windows