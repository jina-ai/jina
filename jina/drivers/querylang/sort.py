__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable

from . import QueryLangDriver
from ...helper import rgetattr

if False:
    from ...proto import jina_pb2


class SortQL(QueryLangDriver):
    """Restrict the size of the ``matches`` to ``k`` (given by the request)

    This driver works on both chunk and doc level
    """

    def __init__(self, field: str, reverse: bool = False, *args, **kwargs):
        """

        :param reverse: sort the value from big to small
        """

        super().__init__(*args, **kwargs)
        self._reverse = reverse
        self._field = field

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        docs.sort(key=lambda x: rgetattr(x, self.field), reverse=self.reverse)

