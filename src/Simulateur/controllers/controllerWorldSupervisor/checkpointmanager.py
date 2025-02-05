from typing import List
from checkpoint import Checkpoint
from controller import Supervisor


class CheckpointManager:
    def __init__(self, supervisor: Supervisor, checkpoints: List[Checkpoint]):
        self.supervisor = supervisor
        self.checkpoints = checkpoints
        self.next_checkpoint = 0
        for checkpoint in self.checkpoints:
            checkpoint.create_vector_2d(self.supervisor)

    def update(self, x, y):
        """
        Update the next checkpoint if the vehicle has reached the current one
        """
        checkpoint = self.checkpoints[self.next_checkpoint]
        if checkpoint.check_plane(x, y):
            self.next_checkpoint = (self.next_checkpoint + 1) % len(self.checkpoints)
            return True
        return False

    def reset(self):
        self.next_checkpoint = 0


checkpoints = [
    Checkpoint(0, -0.314494, -2.47211), # this one is very close to the beginning of the track
    Checkpoint(0, 1.11162, -2.56708),
    Checkpoint(0.8, 2.54552, -2.27446),
    Checkpoint(1.2, 3.58779, -1.38814),
    Checkpoint(1.57, 3.58016, -0.0800134),
    Checkpoint(2.2, 3.23981, 1.26309),
    Checkpoint(1.57, 2.8261, 1.99783),
    Checkpoint(1.04, 3.18851, 2.71151),
    Checkpoint(2.5, 3.6475, 4.09688),
    Checkpoint(-3, 2.58692, 4.5394),
    Checkpoint(-2.5, 1.52457, 4.3991),
    Checkpoint(-2.2, 0.659969, 3.57074),
    Checkpoint(-1.9, 0.000799585, 2.90417),
    Checkpoint(-1, 0.0727115, 1.81299),
    Checkpoint(-1, 0.788956, 1.22248),
    Checkpoint(-1.6, 1.24749, 0.288391),
    Checkpoint(-3, 0.0789172, -0.557653),
    Checkpoint(2.7, -0.832859, -0.484867),
    Checkpoint(1.8, -1.79723, 0.408769),
    Checkpoint(1.6, -1.7446, 1.3386),
    Checkpoint(2.2, -1.92104, 2.72452),
    Checkpoint(3, -2.96264, 2.96666),
    Checkpoint(-2.2, -4.19027, 2.74619),
    Checkpoint(-1.6, -4.34725, 1.7503),
    Checkpoint(-1.57, -4.26858, 0.259482),
    Checkpoint(-1.4, -4.20936, -1.06968),
    Checkpoint(-0.8, -4.0021, -2.35518),
    Checkpoint(-0.3, -2.89371, -2.49154),
    Checkpoint(0, -2.01029, -2.51669),
]
