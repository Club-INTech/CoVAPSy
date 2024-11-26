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

        print("self.getName(): ", self.getName())
        self.i = int(self.getName().split("_")[-1])

        # Lidar
        self.lidar = self.getDevice("RpLidarA2")
        self.lidar.enable(self.sensorTime)
        self.lidar.enablePointCloud()

        # Distance sensors
        self.front_center_sensor = self.getDevice("front_center_sensor")
        self.side_left_sensor = self.getDevice("side_left_sensor")
        self.side_right_sensor = self.getDevice("side_right_sensor")
        self.front_center_sensor.enable(self.sensorTime)
        self.side_left_sensor.enable(self.sensorTime)
        self.side_right_sensor.enable(self.sensorTime)

        # Checkpoint sensor
        self.up_sensor = self.getDevice("up_sensor")
        self.up_sensor.enable(self.sensorTime)

        # Communication
        self.receiver = self.getDevice("TT02_receiver")
        print(f"{self.receiver=}")
        self.receiver.enable(self.sensorTime)
        self.receiver.setChannel(2 * self.i) # corresponds the the supervisor's emitter channel
        self.emitter = self.getDevice("TT02_emitter")
        print(f"{self.emitter=}")
        self.emitter.setChannel(2 * self.i + 1) # corresponds the the supervisor's receiver channel

        # Last data received from the supervisor (steering angle)
        self.last_data = 0.

    #Vérification de l"état de la voiture
    def observe(self):
        try:
            #Division par 10 pour que la valeur soient entre 0 et 1
            return np.array(self.lidar.getRangeImage(), dtype=np.float32)/10
        except: #En cas de non retour lidar
            print("Pas de retour du lidar")
            return np.zeros(self.lidar.getNumberOfPoints(), dtype=np.float32)

    #Fonction step de l"environnement GYM
    def step(self):
        # sends observation to the supervisor
        self.emitter.send(self.observe().tobytes())

        if self.receiver.getQueueLength() > 0:
            while self.receiver.getQueueLength() > 1:
                self.receiver.nextPacket()
            self.last_data = np.frombuffer(self.receiver.getBytes(), dtype=np.float32)[0]

        steeringAngle = self.last_data
        print(f"steeringAngle({self.i}): ", steeringAngle)
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
