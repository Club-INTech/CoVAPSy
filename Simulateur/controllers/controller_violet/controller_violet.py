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

#Lidar
lidar = Lidar("Hokuyo")
lidar.enable(basicTimeStep // 4)
lidar.enablePointCloud()

touch_sensor = driver.getDevice("touch_sensor")
touch_sensor.enable(basicTimeStep)

# vitesse en km/h
speed = 0
maxSpeed = 28 #km/h

# angle de la direction
angle = 0
maxangle = 0.28 #rad (étrange, la voiture est défini pour une limite à 0.31 rad...

# mise a zéro de la vitesse et de la direction
driver.setSteeringAngle(angle)
driver.setCruisingSpeed(speed)

while driver.step() != -1:
    speed = driver.getTargetCruisingSpeed()
    donnees_lidar = np.nan_to_num(lidar.getRangeImage(), nan=0., posinf=30.)
    sensor_data = touch_sensor.getValue()

    # goes backwards
    if sensor_data == 1:
        backwards_duration = 1000 # ms
        for _ in range(backwards_duration // basicTimeStep):
            speed = -1
            angle = np.sign(donnees_lidar[-32]-donnees_lidar[32]) * 0.2
            print(angle)
            driver.setCruisingSpeed(speed)
            driver.setSteeringAngle(0)
            driver.step()


    speed = 3 #km/h
    #l'angle de la direction est la différence entre les mesures des rayons
    angle = np.sign(donnees_lidar[32]-donnees_lidar[-32]) * 0.2
    print(angle)
    # clamp speed and angle to max values
    if speed > maxSpeed:
        speed = maxSpeed
    elif speed < -1 * maxSpeed:
        speed = -1 * maxSpeed
    if angle > maxangle:
        angle = maxangle
    elif angle < -maxangle:
        angle = -maxangle

    driver.setCruisingSpeed(speed)
    driver.setSteeringAngle(angle)
