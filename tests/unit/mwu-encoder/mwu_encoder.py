from typing import Any

import numpy as np

from jina.executors.encoders import BaseEncoder


class MWUEncoder(BaseEncoder):
    def __init__(self, greetings: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._greetings = greetings

    def encode(self, content: 'np.ndarray', *args, **kwargs) -> Any:
        self.logger.info(f'{self._greetings} {content}')
        return np.random.random([content.shape[0], 3])


class MWUUpdater(BaseEncoder):
    def __init__(self, greetings: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._greetings = greetings

    def encode(self, content: Any, *args, **kwargs) -> Any:
        self.is_updated = True
        return np.random.random([content.shape[0], 3])
