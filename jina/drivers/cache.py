__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable

import numpy as np

from . import BaseRecursiveDriver
from ..proto import uid

if False:
    from ..proto import jina_pb2


class UniqueDocDriver(BaseRecursiveDriver):
    """ Remove docs that previously have seen in the cache.

    :class:UniqueDocDriver: follows a simple rule: it stores all new doc.id in a cache file.
    If a doc.id hits the cache, then it is removed from the request.
    """

    def __init__(self, ids_file: str, *args, **kwargs):
        """

        :param ids_file: a file path to store observed doc ids
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self._ids_history = ids_file

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs) -> None:
        if len({d.id for d in docs}) != len(docs):
            raise ValueError('doc id is not unique')

        hit_idx = []
        with open(self._ids_history, 'ab+') as fp:
            fp.seek(0)
            _ids = np.frombuffer(fp.read(), dtype=np.int64)
            fp.seek(0, 2)
            for idx, doc in enumerate(docs):
                if uid.id2hash(doc.id) not in _ids:
                    fp.write(uid.id2bytes(doc.id))
                else:
                    hit_idx.append(idx)

        # delete hit docs in reverse
        for j in reversed(hit_idx):
            del docs[j]
