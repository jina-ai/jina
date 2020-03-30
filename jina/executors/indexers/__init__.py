import os
from typing import Tuple

import numpy as np

from .. import BaseExecutor
from ...helper import call_obj_fn


class BaseIndexer(BaseExecutor):
    """``BaseIndexer`` stores and searches with vectors.

    The key functions here are :func:`add` and :func:`query`.
    One can decorate them with :func:`jina.decorator.require_train`,
    :func:`jina.helper.batching` and :func:`jina.logging.profile.profiling`.

    .. seealso::
        :mod:`jina.drivers.handlers.index`

    .. note::
        Calling :func:`save` to save a :class:`BaseIndexer` will create
        more than one files. One is the serialized version of the :class:`BaseIndexer` object, often ends with ``.bin``

    .. warning::
        When using :class:`BaseIndexer` out of the Pod, use it with context manager

        .. highlight:: python
        .. code-block:: python

            with BaseIndexer() as b:
                b.add()

        So that it can safely save the data. Or you have to manually call `b.close()` to close the indexer safely.
    """

    def __init__(self,
                 index_filename: str,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index_filename = index_filename  #: the file name of the stored index, no path is required
        self._size = 0

    def add(self, keys: 'np.ndarray', vectors: 'np.ndarray', *args, **kwargs):
        """Add new chunks and their vector representations

        :param keys: ``chunk_id`` in 1D-ndarray, shape B x 1
        :param vectors: vector representations in B x D
        """
        pass

    def post_init(self):
        """query handler and write handler can not be serialized, thus they must be put into :func:`post_init`. """
        self._query_handler = None
        self._write_handler = None

    def query(self, vectors: 'np.ndarray', top_k: int, *args, **kwargs) -> Tuple['np.ndarray', 'np.ndarray']:
        """Find k-NN using query vectors, return chunk ids and chunk scores

        :param vectors: query vectors in ndarray, shape B x D
        :param top_k: int, the number of nearest neighbour to return
        :return: a tuple of two ndarray.
            The first is ids in shape B x K (`dtype=int`), the second is scores in shape B x K (`dtype=float`)
        """
        pass

    @property
    def index_abspath(self) -> str:
        """Get the file path of the index storage

        """
        return self.get_file_from_workspace(self.index_filename)

    @property
    def query_handler(self):
        """A readable and indexable object, could be dict, map, list, numpy array etc. """
        if self._query_handler is None and os.path.exists(self.index_abspath):
            self._query_handler = self.get_query_handler()

        if self._query_handler is None:
            self.logger.warning(f'you can not query from {self} as its "query_handler" is not set. '
                                'If you are indexing data then that is fine, just means you can not do querying-while-indexing.'
                                'If you are querying data then the index file must be broken.')
        return self._query_handler

    @property
    def write_handler(self):
        """A writable and indexable object, could be dict, map, list, numpy array etc. """

        if self._write_handler is None:
            if os.path.exists(self.index_abspath):
                self._write_handler = self.get_add_handler()
            else:
                self._write_handler = self.get_create_handler()
        if self._write_handler is None:
            self.logger.warning('"write_handler" is None, you may not add data to this index, '
                                'unless "write_handler" is later assigned with a meaningful value')
        return self._write_handler

    def get_query_handler(self):
        """Get a *readable* index handler when the ``index_abspath`` already exist, need to be overrided
        """
        raise NotImplementedError

    def get_add_handler(self):
        """Get a *writable* index handler when the ``index_abspath`` already exist, need to be overrided"""
        raise NotImplementedError

    def get_create_handler(self):
        """Get a *writable* index handler when the ``index_abspath`` does not exist, need to be overrided"""
        raise NotImplementedError

    @property
    def size(self) -> int:
        """The number of vectors/chunks indexed """
        return self._size

    def __getstate__(self):
        d = super().__getstate__()
        self.flush()
        return d

    def close(self):
        """Close all file-handlers and release all resources. """
        self.flush()
        call_obj_fn(self.write_handler, 'close')
        call_obj_fn(self.query_handler, 'close')
        super().close()

    def flush(self):
        """Flush all buffered data to ``index_abspath`` """
        call_obj_fn(self.write_handler, 'flush')
