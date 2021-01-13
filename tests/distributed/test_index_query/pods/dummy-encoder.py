__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from jina.executors.encoders import BaseEncoder
from jina.executors.decorators import batching


class DummyEncoder(BaseEncoder):
    def __init__(self,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

    @batching(batch_size=1)
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        return np.random.random((1, 3))
