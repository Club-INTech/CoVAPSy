import torch
from torch.utils.data import IterableDataset


class FifoDataset(IterableDataset):
    def __init__(self, fifo_path):
        super(FifoDataset, self).__init__()
        self.fifo_path = fifo_path

    def __iter__(self):
        # Open the FIFO in read mode
        with open(self.fifo_path, 'rb') as fifo:
            while True:
                try:
                    # Deserialize and yield the data
                    data = torch.load(fifo)
                    yield data
                except EOFError:
                    break  # Stop iteration on FIFO read error
