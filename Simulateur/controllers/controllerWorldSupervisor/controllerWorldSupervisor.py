from typing import *
import numpy as np
import random
import gymnasium as gym
import time

from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv
from stable_baselines3.common.env_util import make_vec_env

from controller import Supervisor

S = Supervisor()

class WebotsGymEnvironment(gym.Env):
    """
    One environment for each vehicle

    n: index of the vehicle
    supervisor: the supervisor of the simulation
    """

    def __init__(self, i: int, lidar_horizontal_resolution: int):
        print("CALLING __init__ WITH i = ", i)
        print("trying to get supervisor", flush=True)
        self.supervisor = S
        print("supervisor acquired", flush=True)
        self.i = i
        self.lidar_horizontal_resolution = lidar_horizontal_resolution

        basicTimeStep = int(self.supervisor.getBasicTimeStep())
        self.sensorTime = basicTimeStep // 4

        #Paramètre de la voiture (position, etc..)
        print("trying to create car", flush=True)

        self.emitter = self.supervisor.getDevice("emitter")

        self.action_space = gym.spaces.Discrete(5) #actions disponibles
        min = np.zeros(self.lidar_horizontal_resolution)
        max = np.ones(self.lidar_horizontal_resolution)
        self.observation_space = gym.spaces.Box(min, max, dtype=np.float32) #Etat venant du LIDAR
        print(self.observation_space)
        print(self.observation_space.shape)

        print("__init__ done")

    # returns the lidar data of all vehicles
    def observe(self):
        res =  np.array([
            self.vehicle.getField("lidarData").getMFFloat(i)
            for i in range(self.lidar_horizontal_resolution)
        ], dtype=np.float32)
        return res

    # reset the gym environment
    def reset(self, seed=0):
        #Valeur aléatoire
        # car width: 0.25
        y = -3.2 + self.i * 0.25
        INITIAL_trans = [-1, y, 0.0399538]
        INITIAL_rot = [-0.304369, -0.952554, -8.76035e-05 , 6.97858e-06]

        # WARNING: this is not thread safe
        vehicle = self.supervisor.getFromDef(f"TT02_{self.i}")
        vehicle.getField("translation").setSFVec3f(INITIAL_trans)
        vehicle.getField("rotation").setSFRotation(INITIAL_rot)

        time.sleep(0.3) #Temps de pause après réinitilialisation

        obs = self.observe()
        print(obs.shape)
        #super().step()
        info = {}
        return obs, info

    # step function of the gym environment
    def step(self, action):
        #print("Action: ", action)
        print("Steering angle: ", [-0.3, -0.1, 0.0, 0.1, 0.3][action])
        steeringAngle = [-0.3, -0.1, 0.0, 0.1, 0.3][action]
        self.vehicle.getField("steeringAngleInstruction").setSFFloat(steeringAngle)
        # we should add a beacon sensor pointing upwards to detect the beacon

        obs = self.observe()

        reward = 0
        done = False
        truncated = False

        front, left, right, up = [self.vehicle.getField("distanceSensorData").getMFFloat(i) for i in range(4)]

        if front >= 900 and not(done):
            print("Collision avant")
            reward = -100
            done = True
        elif ((front >= 854 and left >= 896) or (front >= 696 and left >= 910) or left >= 937) and not(done):
            print("Collision gauche")
            reward = -100
            done = True
        elif ((front >= 850 and right >= 893) or (front >= 584 and right >= 910) or right >= 961) and not(done):
            print("Collision droite")
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
            f'    translation -1 -2.5 0.04' \
            f'    name "TT02_{i}"' \
            f'    controller "controllerVehicleDriver"' \
            f'    color 0.5 0 0.6' \
            f'    lidarHorizontalResolution {lidar_horizontal_resolution}' \
            f'    steeringAngleInstruction 0' \
            f'    lidarData [{lidar_horizontal_resolution * ' 0. '}]' \
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


    env = DummyVecEnv([lambda i=i: WebotsGymEnvironment(i, lidar_horizontal_resolution) for i in range(n_envs)])


    print("Environment created")
    # check_env(env)

    logdir = "./Webots_tb/"
    #-- , tensorboard_log = logdir -- , tb_log_name = "PPO_voiture_webots"

    #Définition modèle avec paramètre par défaut
    model = PPO("MlpPolicy", env,
        n_steps=2048,
        n_epochs=10,
        batch_size=32,
        learning_rate=3e-3,
        verbose=1,
        device="cuda:0"
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
