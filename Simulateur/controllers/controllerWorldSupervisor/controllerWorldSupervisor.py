from typing import *
import numpy as np
import random
import gymnasium as gym
import time
from threading import Lock
from torch.cuda import is_available

from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv

from controller import Supervisor

S = Supervisor()

class WebotsGymEnvironment(gym.Env):
    """
    One environment for each vehicle

    n: index of the vehicle
    supervisor: the supervisor of the simulation
    """

    def __init__(self, i: int, lidar_horizontal_resolution: int, emitter_lock: Lock, receiver_lock: Lock, reset_lock: Lock):
        self.supervisor = S
        self.i = i
        self.lidar_horizontal_resolution = lidar_horizontal_resolution
        self.n_sensors = 1

        basicTimeStep = int(self.supervisor.getBasicTimeStep())
        self.sensorTime = basicTimeStep // 4

        self.reset_lock = reset_lock

        # Emitters
        self.emitter = self.supervisor.getDevice("supervisor_emitter")
        self.emitter_lock = emitter_lock
        self.emitter_channel = 2 * self.i

        # Receivers
        self.receiver = self.supervisor.getDevice("supervisor_receiver")
        self.receiver.enable(self.sensorTime)
        self.receiver_lock = receiver_lock
        self.receiver_channel = 2 * self.i + 1

        # Last data received from the car
        self.last_data = np.zeros(self.lidar_horizontal_resolution + self.n_sensors, dtype=np.float32)

        self.action_space = gym.spaces.Discrete(5) #actions disponibles
        min = np.zeros(self.n_sensors + self.lidar_horizontal_resolution)
        max = np.ones(self.n_sensors + self.lidar_horizontal_resolution)
        self.observation_space = gym.spaces.Box(min, max, dtype=np.float32) #Etat venant du LIDAR
        print(self.observation_space)
        print(self.observation_space.shape)

    # returns the lidar data of all vehicles
    def observe(self):
        # gets from Receiver
        with self.receiver_lock:
            if self.receiver.getQueueLength() > 0:
                self.receiver.setChannel(self.receiver_channel)

                while self.receiver.getQueueLength() > 1:
                    self.receiver.nextPacket()

        return self.last_data

    # reset the gym environment
    def reset(self, seed=0):
        #Valeur aléatoire
        # car width: 0.25
        y = -3.2 + self.i * 0.25
        INITIAL_trans = [-1, y, 0.0399538]
        INITIAL_rot = [-0.304369, -0.952554, -8.76035e-05 , 6.97858e-06]

        # WARNING: this is not thread safe
        with self.reset_lock:
            vehicle = self.supervisor.getFromDef(f"TT02_{self.i}")
            vehicle.getField("translation").setSFVec3f(INITIAL_trans)
            vehicle.getField("rotation").setSFRotation(INITIAL_rot)

        obs = self.observe()
        #super().step()
        info = {}
        return obs, info

    # step function of the gym environment
    def step(self, action):
        #print("Action: ", action)
        steeringAngle = [-0.3, -0.1, 0.0, 0.1, 0.3][action]
        with self.emitter_lock:
            self.emitter.setChannel(self.emitter_channel)
            self.emitter.send(np.array([steeringAngle], dtype=np.float32).tobytes())

        # we should add a beacon sensor pointing upwards to detect the beacon

        obs = self.observe()
        sensor_data = obs[:self.n_sensors]

        reward = 0
        done = False
        truncated = False

        b_collided, = distance_data
        up = 0

        if b_collided and not(done):
            print("Collision avant")
            reward = -100
            done = True
        elif up > 700:
            done = False
            print("Balise passée")
            reward = 20
        else:
            done = False
            reward = 0

        self.supervisor.step()

        return obs, reward, done, truncated, {}

    #Fonction render de l"environnement GYM
    def render(self, mode="human", close=False):
        pass


def create_vehicles(n_envs: int, lidar_horizontal_resolution: int):
    root = S.getRoot()
    children_field = root.getField("children")

    for i in range(n_envs):
        proto_string = \
            f'DEF TT02_{i} TT02_2023b' '{' \
            f'    name "TT02_{i}"' \
            f'    controller "controllerVehicleDriver"' \
            f'    color 0.5 0 0.6' \
            f'    lidarHorizontalResolution {lidar_horizontal_resolution}' \
            '}'

        print("Spawning vehicle:", flush=True)
        print(proto_string, flush=True)

        index = children_field.importMFNodeFromString(-1, proto_string)
        print("Vehicle spawned")

#----------------Programme principal--------------------
def main():
    n_envs = 1
    lidar_horizontal_resolution = 512
    print("Creating environment")
    create_vehicles(n_envs, lidar_horizontal_resolution)


    # global i
    # i = -1
    # def f():
    #     global i
    #     i += 1
    #     return WebotsGymEnvironment(i, lidar_horizontal_resolution)
    # env = make_vec_env(
    #     f,
    #     n_envs=n_envs,
    #     vec_env_cls=SubprocVecEnv
    # )

    emitter_lock = Lock()
    receiver_lock = Lock()
    reset_lock = Lock()
    env = DummyVecEnv([lambda i=i: WebotsGymEnvironment(i, lidar_horizontal_resolution, emitter_lock, receiver_lock, reset_lock) for i in range(n_envs)])


    print("Environment created")
    # check_env(env)

    logdir = "./Webots_tb/"
    #-- , tensorboard_log = logdir -- , tb_log_name = "PPO_voiture_webots"

    #Définition modèle avec paramètre par défaut
    model = PPO("MlpPolicy", env,
        n_steps=2048,
        n_epochs=1, # doesn't make sense here
        batch_size=32,
        learning_rate=3e-3,
        verbose=1,
        device="cuda:0" if is_available() else "cpu"
    )

    #Entrainnement
    model.learn(total_timesteps=1e6)

    #Sauvegarde
    model.save("Voiture_autonome_Webots_PPO")

    #del model

    #Chargement des données d"apprentissage
    #model = PPO.load("Voiture_autonome_Webots_PPO")

    obs = env.reset()

    for _ in range(1000000):
        #Prédiction pour séléctionner une action à partir de l"observation
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, done, info = env.step(action)
        if done:
            obs = env.reset()


if __name__ == "__main__":
    main()
