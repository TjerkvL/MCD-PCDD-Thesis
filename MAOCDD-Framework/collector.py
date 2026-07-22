# Imports
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
        self.windowSize = window_size
        self.slide = slide

    def __len__(self):

        return max(1, (len(self.dataset) - self.windowSize) // self.slide + 1)

    def __getitem__(self, index):

        startIndex = index * self.slide
        endIndex = startIndex + self.windowSize

        return self.dataset[startIndex:endIndex]


class Collector:

    """
    INPUT:
        windowData: torch.Tensor [T_window, F]

    OUTPUT:
        list of [torch.Tensor] subWindows
    """

    def __init__(
        self,
        window_size,
        sub_window_num,
        min_subwindows,
        max_subwindows,
        comparator
    ):

        self.windowSize = window_size
        self.subWindowNum = sub_window_num
        self.minSubwindows = min_subwindows
        self.maxSubwindows = max_subwindows
        self.comparator = comparator

    # Basic split of a window into smaller sub-windows
    def collect(self, windowData):

        subWindowSize = int(windowData.size(0) / self.subWindowNum)

        return list(torch.split(windowData, subWindowSize))

    # Generate embeddings for a sub-window
    def getEmbedding(self, subWindow):

        samples = self.comparator.generateSamples(subWindow)

        return self.comparator.model(samples).mean(dim=1)

    # Calculate discrepancy between all sub-window pairs
    def computePairwiseDiscrepancy(self, subWindows):

        discrepancies = []

        for i in range(len(subWindows)):

            for j in range(i + 1, len(subWindows)):

                embeddingA = self.getEmbedding(subWindows[i])
                embeddingB = self.getEmbedding(subWindows[j])

                distance = self.comparator.computeNegativeLoss(
                    embeddingA,
                    embeddingB
                )

                discrepancies.append(distance)

        return torch.stack(discrepancies)

    # Remove sub-windows until discrepancy is acceptable
    def shrinkWindow(self, subWindows, threshold):

        while len(subWindows) > self.minSubwindows:

            discrepancies = self.computePairwiseDiscrepancy(subWindows)
            maximumDiscrepancy = torch.max(discrepancies)

            if maximumDiscrepancy <= threshold:
                break

            subWindows = subWindows[1:]

        return subWindows

    # Add candidate sub-windows while discrepancy remains acceptable
    def expandWindow(self, subWindows, candidatePool, threshold):

        while len(subWindows) < self.maxSubwindows and len(candidatePool) > 0:

            expandedWindows = [candidatePool[-1]] + subWindows

            discrepancies = self.computePairwiseDiscrepancy(expandedWindows)
            maximumDiscrepancy = torch.max(discrepancies)

            if maximumDiscrepancy > threshold:
                break

            subWindows = expandedWindows
            candidatePool = candidatePool[:-1]

        return subWindows