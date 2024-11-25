import numpy as np
import random
import gymnasium as gym
import time

from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.vec_env import SubprocVecEnv

from vehicle import Driver


class VehicleDriver(Driver):
    """
    This class is a subclass of the Driver class and is used to control the vehicle.
    It basically receives instructions from the controllerWorldSupervisor and follows them.
    """

    def __init__(self):
        super().__init__()

        basicTimeStep = int(self.getBasicTimeStep())
        self.sensorTime = basicTimeStep // 4

        # this is needed if we want to communicate through node level fields
        print("self.getName(): ", self.getName())

        #Lidar
        self.lidar = self.getDevice("RpLidarA2")
        self.lidar.enable(self.sensorTime)
        self.lidar.enablePointCloud()

        #Capteur de distance
        self.front_center_sensor = self.getDevice("front_center_sensor")
        self.side_left_sensor = self.getDevice("side_left_sensor")
        self.side_right_sensor = self.getDevice("side_right_sensor")
        self.front_center_sensor.enable(self.sensorTime)
        self.side_left_sensor.enable(self.sensorTime)
        self.side_right_sensor.enable(self.sensorTime)

        #Capteur de balise
        self.up_sensor = self.getDevice("up_sensor")
        self.up_sensor.enable(self.sensorTime)

    #Vérification de l"état de la voiture
    def observe(self):
        try:
            tableau = self.lidar.getRangeImage()
            #Division par 10 pour que la valeur soient entre 0 et 1
            etat = np.array(tableau, dtype=np.float32)/10
        except: #En cas de non retour lidar
            print("Pas de retour du lidar")
            etat = np.zeros(self.lidar.getNumberOfPoints(), dtype=np.float32)

        return etat

    #Fonction step de l"environnement GYM
    def step(self):
        #steeringAngle = self.car.getField("steeringAngleInstruction").getSFFloat()
        steeringAngle = 0
        print("steeringAngle: ", steeringAngle)
        self.setSteeringAngle(steeringAngle)
        self.setCruisingSpeed(2)

        return super().step()

    def run(self):
        while self.step() != -1:
            pass


#----------------Programme principal--------------------
def main():
    print("VehicleDriver init")
    driver = VehicleDriver()
    driver.run()


if __name__ == "__main__":
    main()
