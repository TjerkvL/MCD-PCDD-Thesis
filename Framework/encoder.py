import torch.nn as nn

class Encoder(nn.Module):
    """
    INPUT:
        x: torch.Tensor [k, n, F]
    OUTPUT:
        embeddings: torch.Tensor [k, n, d]
    """

    def __init__(self, input_size, hidden_size, output_size):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, output_size)
        )

    def forward(self, x):
        return self.net(x)