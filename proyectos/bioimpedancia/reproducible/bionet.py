"""Arquitectura recuperada de la tesis; entrenamiento nuevo en experimento.py."""
from torch import nn

class BioNet(nn.Module):
    """
    600 -> 512 -> 256 -> 128 -> 64 -> 5
    input_size=600: 6 bloques de 100 features temporales
    """
    def __init__(self, input_size=600, n_params=5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, 512),
            nn.BatchNorm1d(512), nn.ReLU(), nn.Dropout(0.15),
            nn.Linear(512, 256),
            nn.BatchNorm1d(256), nn.ReLU(), nn.Dropout(0.15),
            nn.Linear(256, 128),
            nn.BatchNorm1d(128), nn.ReLU(), nn.Dropout(0.10),
            nn.Linear(128, 64),  nn.ReLU(),
            nn.Linear(64, n_params)
        )

    def forward(self, x):
        return self.net(x)
