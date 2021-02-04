import inspect
from typing import Dict, List

from .. import BaseExecutor
from ...helper import typename


class BaseSegmenter(BaseExecutor):
    """:class:`BaseSegmenter` works on doc-level,
        it chunks Documents into set of Chunks """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required_keys = {k for k in inspect.getfullargspec(self.segment).args if k != 'self'}
        if not self.required_keys:
            self.logger.warning(f'{typename(self)} works on keys, but no keys are specified')

    def segment(self, *args, **kwargs) -> List[Dict]:
        """
        :return: a list of chunks-level info represented by a dict
        """
        raise NotImplementedError
