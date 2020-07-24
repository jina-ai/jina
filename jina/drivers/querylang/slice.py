__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable

from .. import BaseRecursiveDriver

if False:
    from ...proto import jina_pb2


class SliceQL(BaseRecursiveDriver):
    """Restrict the size of the ``matches`` to ``k`` (given by the request)

    This driver works on both chunk and doc level
    """

    def __init__(self, start: int, end: int = None, *args, **kwargs):
        """

        :param start: Zero-based index at which to start extraction.
        :param end:  Zero-based index before which to end extraction.
                slice extracts up to but not including end. For example, take(1,4) extracts
                the second element through the fourth element (elements indexed 1, 2, and 3).
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.start = start
        self.end = end

    def apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        if self.start <= 0 and (self.end is None or self.end >= len(docs)):
            pass
        else:
            del docs[self.end:]
            del docs[:self.start]


class SliceMatchesQL(SliceQL):
    def apply(self, doc: 'jina_pb2.Document', *args, **kwargs):
        if self.start <= 0 and (self.end is None or self.end >= len(doc.matches)):
            pass
        else:
            del doc.matches[self.end:]
            del doc.matches[:self.start]

    def apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        pass
