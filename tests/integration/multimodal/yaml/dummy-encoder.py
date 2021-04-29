

import numpy as np

from jina.executors.encoders import BaseEncoder


class DummyEncoder(BaseEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def encode(self, content: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        return content
