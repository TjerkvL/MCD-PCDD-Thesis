import torch

class Sampler:
    """
    INPUT:
        sub_window: torch.Tensor [T, F]
    OUTPUT:
        samples: torch.Tensor [k, n, F]
    """

    def __init__(self, n, k, device):
        self.n = n
        self.k = k
        self.device = device

    def sample(self, sub_window, model=None):
        size = sub_window.size(0)

        idx = torch.randint(0, size, (self.n * self.k,))
        samples = sub_window[idx].clone().detach().requires_grad_(True)

        samples = samples.view(self.k, self.n, -1)
        return samples.to(self.device)