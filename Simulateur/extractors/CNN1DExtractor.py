import torch
import torch.nn as nn
from gymnasium import spaces

from stable_baselines3 import PPO
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor


class CNN1DExtractor(BaseFeaturesExtractor):
    def __init__(self, space: spaces.Box, n_sensors: int, lidar_horizontal_resolution: int, device: str = "cpu"):
        # lidar_horizontal_resolution = 1080
        # n_sensors = 1
        self.n_sensors = n_sensors
        cnn = nn.Sequential(
            # 1080

            # compression block
            nn.Conv1d(1,  64, kernel_size=7, stride=2, padding=3, device=device),
            nn.ReLU(),
            nn.MaxPool1d(3),
            nn.Dropout1d(0.2),
            # 180

            nn.Conv1d(64, 64, kernel_size=3, padding="same", device=device),
            nn.ReLU(),
            nn.MaxPool1d(3),
            nn.Dropout1d(0.3),
            # 60

            nn.Conv1d(64, 128, kernel_size=3, padding="same", device=device),
            nn.ReLU(),
            nn.AvgPool1d(2),
            nn.Dropout1d(0.4),
            # 30

            nn.Conv1d(128, 128, kernel_size=3, padding="same", device=device),
            nn.ReLU(),
            nn.AvgPool1d(2),
            # 15

            nn.Flatten(-2, -1),
            nn.Dropout(0.5),
        )

        # Compute shape by doing one forward pass
        with torch.no_grad():
            n_flatten = cnn(
                torch.zeros([1, lidar_horizontal_resolution], dtype=torch.float32, device=device)
            ).shape[0]
        super().__init__(space, n_flatten)

        # we cannot assign this directly to self.cnn before calling the super constructor
        self.cnn = cnn


    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        return self.cnn(observations[..., None, self.n_sensors:])
