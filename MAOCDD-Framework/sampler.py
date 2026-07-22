# Imports
import torch


class Sampler:

    """
    INPUT:
        subWindow: torch.Tensor [T, F]

    OUTPUT:
        samples: torch.Tensor [k, n, F]
    """

    def __init__(self, n, k, device):
        self.n = n
        self.k = k
        self.device = device

    # Generate random samples from a sub-window
    def sample(self, subWindow, model=None):

        windowSize = subWindow.size(0)

        sampleIndices = torch.randint(0, windowSize, (self.n * self.k,))

        samples = subWindow[sampleIndices].clone().detach().requires_grad_(True)
        samples = samples.view(self.k, self.n, -1)

        return samples.to(self.device)