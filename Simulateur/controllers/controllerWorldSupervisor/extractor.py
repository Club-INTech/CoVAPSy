import torch
import torch.nn as nn
from gymnasium import spaces

from stable_baselines3 import PPO
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor


class CNN1DExtractor(BaseFeaturesExtractor):
    def __init__(self, space: spaces.Box, n_sensors: int, lidar_horizontal_resolution: int, device: str = "cpu"):
        # lidar_horizontal_resolution = 512
        # n_sensors = 1
        cnn = nn.Sequential(
            nn.Conv1d(1,  16, kernel_size=16, stride=8, padding=8, device=device),
            nn.ReLU(),
            nn.Conv1d(16, 32, kernel_size=8, stride=4, padding=4, device=device),
            nn.ReLU(),
            nn.Conv1d(32, 32, kernel_size=4, stride=2, padding=2, device=device),
            nn.ReLU(),
            nn.Flatten(),
            nn.Flatten(),
        )

        # Compute shape by doing one forward pass
        with torch.no_grad():
            n_flatten = cnn(
                torch.zeros([1, lidar_horizontal_resolution], dtype=torch.float32, device=device)
            ).shape

        print(n_flatten)
        super().__init__(space, lidar_horizontal_resolution + n_sensors)

        # we cannot assign this directly to self.cnn before calling the super constructor
        self.cnn = cnn


    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        print("ENTERING FORWARD")
        print(observations.shape)
        x = self.cnn(observations)
        print(x.shape)
        print(x.shape)
        return x
