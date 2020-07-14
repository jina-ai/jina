import ctypes
import random
from collections import Iterator


class BaseCounter(Iterator):
    def __init__(self, seed: int = 0):
        self.seed = seed

    def __next__(self):
        raise NotImplementedError


class SimpleCounter(BaseCounter):
    def __next__(self):
        self.seed += 1
        return self.seed


class RandomUintCounter(BaseCounter):
    def __init__(self, max_val=ctypes.c_uint(-1).value, *args, **kwargs):
        super().__init__()
        self.max_val = max_val

    def __next__(self):
        return random.randint(0, self.max_val)
