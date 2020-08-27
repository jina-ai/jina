__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import ctypes
import random
from typing import Iterator


class BaseCounter(Iterator):
    def __init__(self, seed: int = 0):
        self.seed = seed

    def __next__(self):
        raise NotImplementedError


class SimpleCounter(BaseCounter):
    def __init__(self, seed: int = 0):
        super().__init__(seed)
        # note that zero is reserved
        if self.seed == 0:
            self.seed = 1

    def __next__(self) -> int:
        ret = self.seed
        self.seed += 1
        return ret


class RandomUintCounter(BaseCounter):
    def __init__(self, max_val: int = ctypes.c_uint(-1).value):
        super().__init__()
        self.max_val = max_val
        if self.seed:
            random.seed(self.seed)

    def __next__(self) -> int:
        return random.randint(1, self.max_val)  # zero is reserved
