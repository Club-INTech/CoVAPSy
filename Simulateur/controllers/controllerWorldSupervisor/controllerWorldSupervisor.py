import re
from typing import *
import numpy as np
import random
import gymnasium as gym
import time
import math

from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv

from checkpoint import Checkpoint
from checkpointmanager import CheckpointManager, checkpoints

from controller import Supervisor
supervisor = Supervisor()

import torch.nn as nn

import os
import sys

# this is necessary because we are not in a package context
# so we cannot do from ..config import *
# SO EVEN IF IT LOOKS UGLY, WE HAVE TO DO THIS
script_dir = os.path.dirname(os.path.abspath(__file__))
controllers_path = os.path.join(script_dir, '../..')
sys.path.append(controllers_path)

from config import *

import matplotlib.pyplot as plt
#plt.ion()
# fig, ax = plt.subplots()
# line, = ax.plot([], [])
# plt.xlim(-lidar_max_range, lidar_max_range)
# plt.ylim(-lidar_max_range, lidar_max_range)
# plt.scatter(0, 0, c="red", marker="+")


def log(s: str):
    if DOLOG:
        print(s, file=open("/tmp/autotech/logs", "a"))


# FIFO to communnicate with the train SERVER{simulation_rank} process
# DOES NOT WORK WHEN USING SubProcVecENV
# simulation_rank = int(
#     max(
#         re.findall(
#             r"(\d+)toserver.pipe",
#             "\n".join(os.listdir("/tmp/autotech/")),
#             re.MULTILINE
#         ) or [0]
#     )
# )

with open(f"/proc/{os.getppid()}/status") as f:
    log("youpi j'ai réussi à choper un truc I guess")
    for line in f:
        log(line)
        if line.startswith("PPid:"):
            log("found it bro")
            pppid = line.split()[1]
            log(pppid)
            break

log(pppid)

simulation_rank = int(
    re.search(
        pppid + r" (\d+)",
        open("/tmp/autotech/simulationranks", "r").read(),
        re.MULTILINE
    ).group(1)
)


log(f"CLIENT ?{pppid}? {simulation_rank=}")



class WebotsVehicleGymEnvironment(gym.Env):
    """
    One environment for each vehicle

    n: index of the vehicle
    supervisor: the supervisor of the simulation
    """

    def __init__(self, vehicle_rank: int):
        #print the exported node string

        self.vehicle_rank = vehicle_rank
        self.checkpoint_manager = CheckpointManager(supervisor, checkpoints)

        basicTimeStep = int(supervisor.getBasicTimeStep())
        self.sensorTime = basicTimeStep // 4

        # negative value so that the first reset is not skipped
        self.last_reset = -1e6

        # Emitter
        self.emitter = supervisor.getDevice(f"supervisor_emitter_{vehicle_rank}")
        self.emitter.setChannel(2 * self.vehicle_rank)

        # Receiver
        self.receiver = supervisor.getDevice(f"supervisor_receiver_{vehicle_rank}")
        self.receiver.enable(self.sensorTime)
        self.receiver.setChannel(2 * self.vehicle_rank + 1)


        log(f"CLIENT{simulation_rank}/{vehicle_rank} : begins init")
        log(f"CLIENT{simulation_rank}/{vehicle_rank} : {simulation_rank}toserver.pipe")
        self.fifo_w = open(f"/tmp/autotech/{simulation_rank}toserver.pipe", "wb")
        log(f"CLIENT{simulation_rank}/{vehicle_rank} : serverto{simulation_rank}.pipe")
        self.fifo_r = open(f"/tmp/autotech/serverto{simulation_rank}.pipe", "rb")

        # Last data received from the car
        self.last_data = np.zeros(lidar_horizontal_resolution + n_sensors, dtype=np.float32)

        self.translation_field = supervisor.getFromDef(f"TT02_{self.vehicle_rank}").getField("translation") # may cause access issues ...
        self.rotation_field = supervisor.getFromDef(f"TT02_{self.vehicle_rank}").getField("rotation") # may cause access issues ...

        box_min = np.zeros(n_sensors + lidar_horizontal_resolution)
        box_max = np.ones(n_sensors + lidar_horizontal_resolution)
        self.observation_space = gym.spaces.Box(box_min, box_max, dtype=np.float32) #Etat venant du LIDAR

    # returns the lidar data of all vehicles
    def observe(self):
        # gets from Receiver
        if self.receiver.getQueueLength() > 0:
            while self.receiver.getQueueLength() > 1:
                self.receiver.nextPacket()
            self.last_data = np.frombuffer(self.receiver.getBytes(), dtype=np.float32)

        return self.last_data

    # reset the gym environment reset
    def reset(self, seed=0):
        # this has to be done otherwise thec cars will shiver for a while sometimes when respawning and idk why
        if supervisor.getTime() - self.last_reset >= 1e-1:
            self.last_reset = supervisor.getTime()

            vehicle = supervisor.getFromDef(f"TT02_{self.vehicle_rank}")

            trans = self.checkpoint_manager.getTranslation()
            rot = self.checkpoint_manager.getRotation()

            # trans[0] -= math.cos(rot[3]) * 0.05
            # trans[1] -= math.sin(rot[3]) * 0.05

            self.checkpoint_manager.reset()
            self.translation_field.setSFVec3f(trans)
            self.rotation_field.setSFRotation(rot)
            self.checkpoint_manager.update()

            vehicle.resetPhysics()

        obs = self.observe()
        info = {}
        log(f"CLIENT{simulation_rank}/{self.vehicle_rank} : reset over")
        return obs, info

    # step function of the gym environment
    def step(self, action):
        action_steering = np.linspace(-.44, .44, n_actions_steering, dtype=np.float32)[action[0], None]
        action_speed = np.linspace(0.5, 7.0, n_actions_speed, dtype=np.float32)[action[1], None]
        self.emitter.send(np.array([action_steering, action_speed], dtype=np.float32).tobytes())

        # we should add a beacon sensor pointing upwards to detect the beacon
        obs = self.observe()
        sensor_data = obs[:n_sensors]

        reward = 0
        done = np.False_
        truncated = np.False_

        x, y, z = self.translation_field.getSFVec3f()
        b_past_checkpoint = self.checkpoint_manager.update(x, y)
        b_collided, = sensor_data # unpack sensor data

        if b_collided or (z < -10):
            #print(f"CLIENT{simulation_rank}/{self.vehicle_rank} : {b_collided=}, {z=}")
            reward = np.float32(-2.0)
            done = np.True_
        elif b_past_checkpoint:
            reward = np.float32(1.0) #* np.cos(self.checkpoint_manager.getAngle() - self.rotation_field.getSFRotation()[3], dtype=np.float32)
            done = np.False_
        else:
            reward = np.float32(0.05)
            done = np.False_

        return obs, reward, done, truncated, {}


#----------------Programme principal--------------------
def main():

    envs = [WebotsVehicleGymEnvironment(i) for i in range(n_vehicles)]
    log(f"CLIENT ALL : envs created")
    # check_env(env)

    logdir = "./Webots_tb/"

    log(f"CLIENT ALL : {envs=}")
    supervisor.step()
    log("-------------------------------------------------------------------")
    for i, e in enumerate(envs):
        log(f"CLIENT{simulation_rank}/{e.vehicle_rank} : reset")
        e.reset()


    while supervisor.step() != -1:
        log(f"CLIENT ALL : begin step")
        #Prédiction pour séléctionner une action à partir de l"observation
        for e in envs:
            log(f"CLIENT{simulation_rank}/{e.vehicle_rank} : trying to read from fifo")
            action = np.frombuffer(e.fifo_r.read(np.dtype(np.int64).itemsize * 2), dtype=np.int64)
            log(f"CLIENT{simulation_rank}/{e.vehicle_rank} : received {action=}")
            obs, reward, done, truncated, info = e.step(action)

            if done: obs, info = e.reset()

            log(f"CLIENT{simulation_rank}/{e.vehicle_rank} : sending {obs=}")
            e.fifo_w.write(obs.tobytes())
            log(f"CLIENT{simulation_rank}/{e.vehicle_rank} : sending {reward=}")
            e.fifo_w.write(reward.tobytes())
            log(f"CLIENT{simulation_rank}/{e.vehicle_rank} : sending {done=}")
            e.fifo_w.write(done.tobytes())
            log(f"CLIENT{simulation_rank}/{e.vehicle_rank} : sending {truncated=}")
            e.fifo_w.write(truncated.tobytes())
            e.fifo_w.flush()


if __name__ == "__main__":
    print("BEGINS MAIN FROM CONTROLLER WORLD SUPERVISOR", flush=True)
    main()
