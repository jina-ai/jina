from typing import Any

from jina.executors.encoders import BaseEncoder


class MWUEncoder(BaseEncoder):

    def __init__(self, greetings: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._greetings = greetings

    def encode(self, data: Any, *args, **kwargs) -> Any:
        self.logger.info('%s %s' % (self._greetings, data.shape))
