import inspect
from typing import Dict, List, Union

from .. import BaseExecutor
from ...helper import typename


class BaseSegmenter(BaseExecutor):
    """:class:`BaseSegmenter` works on doc-level,
    it chunks Documents into set of Chunks
    :param args: Variable length arguments
    :param kwargs: Variable length keyword arguments
    """

    def segment(self, *args, **kwargs) -> Union[List[List[Dict]], List[Dict]]:
        """
        :param args: Variable length arguments
        :param kwargs: Variable length keyword arguments
        """
        raise NotImplementedError
