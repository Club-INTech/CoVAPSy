from typing import *
import numpy as np
import random
import gymnasium as gym
import time

from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.vec_env import SubprocVecEnv

from controller import Supervisor


class WebotsGymEnvironment(gym.Env):

    def __init__(self, n: int, supervisor: Supervisor):
        self.supervisor = supervisor
        self.n = n
        self.lidar_horizontal_resolution = 512

        basicTimeStep = int(self.supervisor.getBasicTimeStep())
        self.sensorTime = basicTimeStep // 4

        #Paramètre de la voiture (position, etc..)
        self.vehicles = []
        self.create_vehicles()

        self.action_space = gym.spaces.Discrete(5) #actions disponibles
        min = np.zeros(self.lidar_horizontal_resolution)
        max = np.ones(self.lidar_horizontal_resolution)
        self.observation_space = gym.spaces.Box(min, max, dtype=np.float32) #Etat venant du LIDAR
        print(self.observation_space)
        print(self.observation_space.shape)

        self.translation_fields = [self.vehicles[i].getField("translation") for i in range(n)]
        self.rotation_fields = [self.vehicles[i].getField("rotation") for i in range(n)] # idk why but if this goes before the lidar it will not work


    def create_vehicles(self):
        """
        copies the default DEF vehicle Robot n_envs times so that they can be controlled independently
        """
        # create a group of n vehicles
        robot = self.supervisor.getFromDef("WorldSupervisor")
        children_field = robot.getField("children")
        for i in range(self.n):
            # looks bad but using triple quotes is even worse
            proto_string = \
                f'DEF TT02_{i} TT02_2023b' '{' \
                f'    translation -1 -2.5 0.04' \
                f'    name "TT02_{i}"' \
                f'    controller "controllerVehicleDriver"' \
                f'    color 0.5 0 0.6' \
                f'    lidarHorizontalResolution {self.lidar_horizontal_resolution}' \
                f'   steeringAngleInstruction 0' \
                f'   lidarData [{self.lidar_horizontal_resolution * ' 0. '}]' \
                 '}'

            print("Spawning vehicle:")
            print(proto_string)

            index = children_field.importMFNodeFromString(-1, proto_string)
            vehicle = children_field.getMFNode(index)
            self.vehicles.append(vehicle)

    # returns the lidar data of all vehicles
    def observe(self):
        res =  np.array([
            [
                v.getField("lidarData").getMFFloat(j)
                for j in range(self.lidar_horizontal_resolution)
            ]
            for v in self.vehicles
        ], dtype=np.float32)
        return res

    # reset the gym environment
    def reset(self, seed=0):
        #Valeur aléatoire
        # car width: 0.25
        for i in range(self.n):
            y = -3.3 + i * 0.25
            INITIAL_trans = [-1, y, 0.0399538]
            INITIAL_rot = [-0.304369, -0.952554, -8.76035e-05 , 6.97858e-06]
            self.translation_fields[i].setSFVec3f(INITIAL_trans)
            self.rotation_fields[i].setSFRotation(INITIAL_rot)

        time.sleep(0.3) #Temps de pause après réinitilialisation

        obs = self.observe()
        print(obs.shape)
        #super().step()
        info = {}
        return obs, info

    # step function of the gym environment
    def step(self, action):
        for vehicle in self.vehicles:
            vehicle.getField("steeringAngleInstruction").setSFFloat([-.3, -.1, 0, .1, .3][action])
            # we should add a beacon sensor pointing upwards to detect the beacon

        obs = self.observe()

        reward = 0
        done = False
        truncated = False

        front, left, right, up = [self.vehicles[0].getField("distanceSensorData").getMFFloat(i) for i in range(4)]

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


#----------------Programme principal--------------------
def main():
    n = 1 # number of vehicles
    env = WebotsGymEnvironment(n)
    check_env(env)

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
