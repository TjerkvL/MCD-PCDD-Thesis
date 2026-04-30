import torch

class AdaptiveWindow:
    def __init__(self, mcd, min_subwindows, max_subwindows):
        self.mcd = mcd
        self.min_subwindows = min_subwindows
        self.max_subwindows = max_subwindows

    def compute_pairwise_discrepancy(self, sub_windows):
        discrepancies = []

        for i in range(len(sub_windows)):
            for j in range(i + 1, len(sub_windows)):
                emb_i = self._embed(sub_windows[i])
                emb_j = self._embed(sub_windows[j])

                dist = self.mcd.compute_negative_loss(emb_i, emb_j)
                discrepancies.append(dist)

        return torch.stack(discrepancies)

    def _embed(self, sub_window):
        samples = self.mcd.generate_samples(sub_window)
        embeddings = self.mcd.model(samples).mean(dim=1)
        return embeddings
    
    def shrink_window(self, sub_windows, threshold):
        """
        Reduce window size if instability is too high.
        Removes oldest sub-windows until stable or min reached.
        """

        while len(sub_windows) > self.min_subwindows:
            discrepancies = self.compute_pairwise_discrepancy(sub_windows)
            max_disc = torch.max(discrepancies)

            print(f"Shrink check: {len(sub_windows)} subwindows")
            print(f"Max discrepancy: {max_disc.item()}")

            if max_disc <= threshold:
                break  # stable

            # Remove oldest sub-window (front)
            sub_windows = sub_windows[1:]

        return sub_windows
    

    def expand_window(self, sub_windows, candidate_pool, threshold):
        """
        Expand window size if stable.
        Adds older sub-windows back if stability holds.
        """

        while len(sub_windows) < self.max_subwindows and len(candidate_pool) > 0:

            # Try adding one older sub-window at the front
            new_sub_windows = [candidate_pool[-1]] + sub_windows

            discrepancies = self.compute_pairwise_discrepancy(new_sub_windows)
            max_disc = torch.max(discrepancies)

            print(f"Expand attempt: {len(sub_windows)} subwindows")
            print(f"Max discrepancy after expand: {max_disc.item()}")

            if max_disc > threshold:
                break  # adding caused instability → stop expanding

            # Accept expansion
            sub_windows = new_sub_windows
            candidate_pool = candidate_pool[:-1]

        return sub_windows