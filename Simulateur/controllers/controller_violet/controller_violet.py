# Copyright 1996-2022 Cyberbotics Ltd.
#
# Controle de la voiture TT-02 simulateur CoVAPSy pour Webots 2023b
# Inspiré de vehicle_driver_altino controller
# Kévin Hoarau, Anthony Juton, Bastien Lhopitallier, Martin Taynaud
# juillet 2023


import numpy as np
from vehicle import Driver
from controller import Lidar


driver = Driver()

basicTimeStep = int(driver.getBasicTimeStep())
sensorTime = basicTimeStep // 4

lidar = Lidar("Hokuyo")
lidar.enable(sensorTime)
lidar.enablePointCloud()

camera = driver.getDevice("RASPI_Camera_V2")
camera.enable(sensorTime)

touch_sensor = driver.getDevice("touch_sensor")
touch_sensor.enable(sensorTime)

# vitesse en km/h
speed = 0
maxSpeed = 28 #km/h

# angle de la direction
angle = 0
maxangle = 0.28 #rad (étrange, la voiture est défini pour une limite à 0.31 rad...

backwards_duration = 2000 # ms
stop_duration = 1000 # ms

death_count = 0

# mise a zéro de la vitesse et de la direction
driver.setSteeringAngle(angle)
driver.setCruisingSpeed(speed)


def backwards(lidar_data, camera_data):
    for _ in range(backwards_duration // basicTimeStep):
        speed = -1
        avg_color = np.mean(camera_data, axis=0)
        if avg_color[0] >= avg_color[1]:
            angle = 0.2
        else:
            angle = -0.2
        driver.setCruisingSpeed(speed)
        driver.setSteeringAngle(angle)
        driver.step()

def stop():
    driver.setCruisingSpeed(0)
    driver.setSteeringAngle(0)
    for _ in range(stop_duration // basicTimeStep):
        driver.step()
    # will be reset by the controllerWorldSupervisor.py


while driver.step() != -1:
    speed = driver.getTargetCruisingSpeed()
    lidar_data = np.nan_to_num(lidar.getRangeImage(), nan=0., posinf=30.)
    camera_data = np.nan_to_num(camera.getImageArray(), nan=0., posinf=30.)
    print(type(camera.getImageArray()))
    sensor_data = touch_sensor.getValue()

    # goes backwards
    if sensor_data == 1:
        death_count += 1
        if death_count < 3:
            print("backwards", driver.getName())
            backwards(lidar_data, camera_data)
        else:
            print("stop", driver.getName())
            death_count = 0
            stop()


    speed = 3 #km/h
    #l'angle de la direction est la différence entre les mesures des rayons
    avg_color = np.mean(camera_data, axis=0)
    if avg_color[0] >= avg_color[1]:
        angle = 0.2
    else:
        angle = -0.2

    driver.setCruisingSpeed(speed)
    driver.setSteeringAngle(angle)
