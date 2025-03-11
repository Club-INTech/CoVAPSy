# just a file that lets us define some constants that are used in multiple files the simulation
from torch.cuda import is_available

n_simulations = 1
n_vehicles = 4
n_stupid_vehicles = 0
n_actions_steering = 16
n_actions_speed = 16
n_sensors = 1
context_size = 128
lidar_horizontal_resolution = 128 # DON'T CHANGE THIS VALUE PLS
camera_horizontal_resolution = 128 # DON'T CHANGE THIS VALUE PLS
lidar_max_range = 12.0
device = "cuda" if is_available() else "cpu"

B_DEBUG = False
