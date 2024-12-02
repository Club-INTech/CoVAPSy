from controller import Supervisor


def create_nodes(n_envs: int, lidar_horizontal_resolution: int, lidar_max_range: float):
    """
    create n_envs vehicles in the simulation
    for each vehicle, create an emitter and a receiver in the supervisor
    """

    S = Supervisor()

    root = S.getRoot()
    root_children_field = root.getField("children")

    proto_string = \
    'DEF WorldSupervisor Robot' '{' \
    '    supervisor TRUE' \
    '    name "WorldSupervisor"' \
    '    controller "controllerWorldSupervisor"' \
    '    children [' + \
    "\n".join([' Emitter  {name "supervisor_emitter_'  + str(i) + '"}' for i in range(n_envs)]) + \
    "\n".join([' Receiver {name "supervisor_receiver_' + str(i) + '"}' for i in range(n_envs)]) + \
    f'    ]' \
    '}'

    print(proto_string)
    root_children_field.importMFNodeFromString(-1, proto_string)

    for i in range(n_envs):
        proto_string = \
            f'DEF TT02_{i} TT02_2023b' '{' \
            f'    name "TT02_{i}"' \
            f'    controller "controllerVehicleDriver"' \
            f'    color 0.5 0 0.6' \
            f'    lidarHorizontalResolution {lidar_horizontal_resolution}' \
            f'    lidarMaxRange {lidar_max_range}' \
            '}'
        root_children_field.importMFNodeFromString(-1, proto_string)


if __name__ == "__main__":
    n_envs = 2
    lidar_horizontal_resolution = 512
    lidar_max_range = 12.0

    create_nodes(n_envs, lidar_horizontal_resolution, lidar_max_range)
