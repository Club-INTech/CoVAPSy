import matplotlib.pyplot as plt
import numpy as np
from stable_baselines3.common.callbacks import BaseCallback
import torch
import torch.nn.functional as F
from config import *

steering_true = (n_actions_steering + 1) // 2

class DynamicActionPlotDistributionCallback(BaseCallback):
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.fig, self.ax = plt.subplots(2, 1, figsize=(10, 8))

        # Steering bars
        self.steering_bars = self.ax[0].bar(range(n_actions_steering), np.zeros(n_actions_steering), color='blue')
        self.steering_avg = [
            self.ax[0].plot([0, 0], [0,  1], color=(i/3, 1 - i/3, 0), label='Average')[0]
            for i in range(4)
        ]
        self.ax[0].set_ylim(0, 1) # Probabilities range from 0 to 1
        self.ax[0].set_title('Steering Action Probabilities')

        # Speed bars
        self.speed_bars = self.ax[1].bar(range(n_actions_speed), np.zeros(n_actions_speed), color='blue')
        self.speed_avg = self.ax[1].plot([0, 0], [0,  1], color='red', label='Average')[0]
        self.ax[1].set_ylim(0, 1)  # Probabilities range from 0 to 1
        self.ax[1].set_title('Speed Action Probabilities')

    def _on_step(self) -> bool:
        global steering_true
        # Get the action probabilities

        obs = self.locals["obs_tensor"].clone().detach()
        with torch.no_grad():
            latent = self.model.policy.features_extractor(obs)
            extracted = self.model.policy.mlp_extractor.policy_net(latent)
            output = self.model.policy.action_net(extracted)[0]

            T =  [0.4, 0.6, 0.8, 1.0]
            steer_probs = torch.softmax(output[:n_actions_steering], dim=-1).to("cpu")
            speed_probs = torch.softmax(output[n_actions_steering:], dim=-1).to("cpu")



            # Update the probabilities
            for i, bar in enumerate(self.steering_bars):
                bar.set_height(steer_probs[i].item())

            for i in range(4):
                steer_probs_T = torch.softmax(output[:n_actions_steering] / T[i], dim=-1).to("cpu")
                steering_avg = (steer_probs_T / steer_probs_T.sum() * torch.arange(16)).sum().item()
                self.steering_avg[i].set_xdata([steering_avg, steering_avg])



            for i, bar in enumerate(self.speed_bars):
                bar.set_height(speed_probs[i].item())

            speed_avg = (speed_probs * torch.arange(n_actions_speed)).sum().item()
            self.speed_avg.set_xdata([speed_avg, speed_avg])

        plt.draw()
        plt.pause(1e-8)

        return True  # Continue training
