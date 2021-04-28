__copyright__ = "Copyright (c) 2021 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict, List, Union

from .. import BaseExecutor


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
