import os
from typing import *

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.multiprocessing as mp

from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv

import gymnasium as gym

from config import *
from extractor import CNN1DExtractor


def log(s: str):
    if DOLOG:
        print(s, file=open("/tmp/autotech/logs", "a"))



class WebotsSimulationGymEnvironment(gym.Env):
    """
    One environment for each vehicle

    n: index of the vehicle
    supervisor: the supervisor of the simulation
    """

    def __init__(self, simulation_rank: int):
        super().__init__()
        self.simulation_rank = simulation_rank
        box_min = np.zeros(n_sensors + lidar_horizontal_resolution)
        box_max = np.ones(n_sensors + lidar_horizontal_resolution)
        self.observation_space = gym.spaces.Box(box_min, box_max, dtype=np.float32) #Etat venant du LIDAR
        self.action_space = gym.spaces.Discrete(n_actions) #actions disponibles

        if not os.path.exists("/tmp/autotech"):
            os.mkdir("/tmp/autotech")

        log(f"SERVER{simulation_rank} : {simulation_rank=}")

        os.mkfifo(f"/tmp/autotech/{simulation_rank}toserver.pipe")
        os.mkfifo(f"/tmp/autotech/serverto{simulation_rank}.pipe")

        #  --mode=fast --minimize --no-rendering --batch --stdout
        os.system(f"""
            webots ~/CoVAPSy_Intech/Simulateur/worlds/piste2.wbt --mode=fast --minimize --batch --stdout &
            echo $! {simulation_rank} >>/tmp/autotech/simulationranks
        """)
        log(f"SERVER{simulation_rank} : {simulation_rank}toserver.pipe")
        self.fifo_r = open(f"/tmp/autotech/{simulation_rank}toserver.pipe", "rb")
        log(f"SERVER{simulation_rank} : serverto{simulation_rank}.pipe")
        self.fifo_w = open(f"/tmp/autotech/serverto{simulation_rank}.pipe", "wb")
        log(f"SERVER{simulation_rank} : fifo opened :D and init done")
        log("-------------------------------------------------------------------")

    def reset(self, seed=0):
        # basically useless function

        # lidar data
        obs = np.zeros(n_sensors + lidar_horizontal_resolution)
        info = {}
        return obs, info

    def step(self, action):
        log(f"SERVER{self.simulation_rank} : sending {action=}")
        self.fifo_w.write(action.tobytes())
        self.fifo_w.flush()

        # communication with the supervisor
        obs         = np.frombuffer(self.fifo_r.read(np.dtype(np.float32).itemsize * (n_sensors + lidar_horizontal_resolution)), dtype=np.float32) # array
        log(f"SERVER{self.simulation_rank} : received {obs=}")
        reward      = np.frombuffer(self.fifo_r.read(np.dtype(np.float32).itemsize), dtype=np.float32)[0] # scalar
        log(f"SERVER{self.simulation_rank} : received {reward=}")
        done        = np.frombuffer(self.fifo_r.read(np.dtype(np.bool).itemsize), dtype=np.bool)[0] # scalar
        log(f"SERVER{self.simulation_rank} : received {done=}")
        truncated   = np.frombuffer(self.fifo_r.read(np.dtype(np.bool).itemsize), dtype=np.bool)[0] # scalar
        log(f"SERVER{self.simulation_rank} : received {truncated=}")
        info        = {}

        return obs, reward, done, truncated, info


if __name__ == "__main__":
    if not os.path.exists("/tmp/autotech/"):
        os.mkdir("/tmp/autotech/")

    os.system('if [ -n "$(ls /tmp/autotech)" ]; then rm /tmp/autotech/*; fi')
    if DOLOG:
        print("Webots started", file=open("/tmp/autotech/logs", "w"))

    def make_env(rank: int):
        log(f"CAREFUL !!! created an SERVER env with {rank=}")
        return WebotsSimulationGymEnvironment(rank)

    envs = SubprocVecEnv([lambda rank=rank : make_env(rank) for rank in range(n_simulations)])

    policy_kwargs = dict(
        features_extractor_class=CNN1DExtractor,
        features_extractor_kwargs=dict(
            n_sensors=n_sensors,
            lidar_horizontal_resolution=lidar_horizontal_resolution,
            device="cuda" if torch.cuda.is_available() else "cpu"
        ),
        activation_fn=nn.ReLU,
    )

    #gamma = 0.5**(S.getBasicTimeStep() * 1e-3 / 5)
    gamma = .975
    print(f"{gamma=}")

    model = PPO("MlpPolicy", envs,
        n_steps=2048,
        n_epochs=10,
        batch_size=64,
        learning_rate=3e-3,
        gamma=gamma, # calculated so that discounts by 1/2 every T seconds
        verbose=1,
        device="cuda" if torch.cuda.is_available() else "cpu",
        policy_kwargs=policy_kwargs
    )


    # NOTE: this is required for the ``fork`` method to work
    # same object as pi_features_extractor and vf_features_extractor
    #model.policy.share_memory()

    log(f"SERVER : finished executing")
    # keep the process running and the fifo open

    model.learn(total_timesteps=1e6)
    # while True:
    #     pass
    # processes = []
    # for rank in range(num_processes):
    #     p = mp.Process(target=train, args=(model,))
    #     p.start()
    #     processes.append(p)
    # for p in processes:
    #     p.join()