import ctypes
import random
from collections import Iterator


class BaseCounter(Iterator):
    def __init__(self, seed: int = 0):
        self.seed = seed

    def __next__(self):
        raise NotImplementedError


class SimpleCounter(BaseCounter):
    def __init__(self, seed: int = 0):
        super().__init__(seed)

    def __next__(self):
        self.seed += 1  # note the first number starts with 1 and zero is reserved
        return self.seed


class RandomUintCounter(BaseCounter):
    def __init__(self, max_val: int = ctypes.c_uint(-1).value):
        super().__init__()
        self.max_val = max_val
        if self.seed:
            random.seed(self.seed)

    def __next__(self):
        return random.randint(1, self.max_val)  # zero is reserved
