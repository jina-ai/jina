from typing import Any

import numpy as np

from jina.executors.encoders import BaseEncoder


class MWUEncoder(BaseEncoder):

    def __init__(self, greetings: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._greetings = greetings
        
    def post_init(self):
        super(MWUEncoder, self).post_init()
        self.logger.success('look at me! %s' % self._greetings)

    def encode(self, data: Any, *args, **kwargs) -> Any:
        self.logger.info('%s %s' % (self._greetings, data))
        return np.random.random([data.shape[0], 3])
