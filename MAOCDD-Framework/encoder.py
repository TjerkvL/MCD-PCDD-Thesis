# Imports
import torch.nn as nn
from torch.nn.utils import spectral_norm


class Encoder(nn.Module):

    """
    INPUT:
        x: [k, n, F]

    OUTPUT:
        embeddings: [k, n, d]
    """

    def __init__(self, input_size, hidden_size, output_size):

        super().__init__()

        self.network = nn.Sequential(
            spectral_norm(nn.Linear(input_size, hidden_size)),
            nn.ReLU(),
            spectral_norm(nn.Linear(hidden_size, output_size))
        )

    def forward(self, x):

        return self.network(x)