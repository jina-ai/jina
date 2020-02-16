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
        the other is the file specified by the ``data_path``.
    """

    def __init__(self,
                 data_path: str,
                 *args, **kwargs):
        """
        :param data_path: the index file path
        """
        super().__init__(*args, **kwargs)
        self.data_path = data_path
        self._size = 0

    def add(self, keys: 'np.ndarray', vectors: 'np.ndarray', *args, **kwargs):
        """Add new chunks and their vector representations

        :param keys: ``chunk_id`` in 1D-ndarray, shape B x 1
        :param vectors: vector representations in B x D
        """
        pass

    def query(self, vectors: 'np.ndarray', top_k: int, *args, **kwargs) -> Tuple['np.ndarray', 'np.ndarray']:
        """Find k-NN using query vectors, return chunk ids and chunk scores

        :param vectors: query vectors in ndarray, shape B x D
        :param top_k: int, the number of nearest neighbour to return
        :return: a tuple of two ndarray.
            The first is ids in shape B x K (`dtype=int`), the second is scores in shape B x K (`dtype=float`)
        """
        pass

    def post_init(self):
        """Load indexed data or create new index from ``data_path``"""
        super().post_init()

        self.query_handler, self.add_handler = self._load_index()

        if self.query_handler is None:
            self.logger.warning('"query_handler" is None, you can not query from it. '
                                'If you are indexing data, that is fine. '
                                'It just means you can not do querying-while-indexing, and you later have to '
                                'switch to query mode to use this index')

        if self.add_handler is None:
            self.logger.warning('"write_handler" is None, you may not add data to this index, '
                                'unless "write_handler" is later assigned with a meaningful value')

    def _load_index(self):
        if hasattr(self, 'data_path') and self.data_path:
            try:
                if not os.path.exists(self.data_path):
                    raise FileNotFoundError('"data_path" %s is not exist' % self.data_path)
                if os.path.isdir(self.data_path):
                    raise IsADirectoryError('"data_path" must be a file path, but %s is a directory' % self.data_path)
                self.logger.info('loading index from %s ...' % self.data_path)
                return self.get_query_handler(), self.get_add_handler()
            except (RuntimeError, FileNotFoundError, IsADirectoryError):
                self.logger.warning('fail to load index from %s, will create an empty one' % self.data_path)
                return None, self.get_create_handler()
            except FileExistsError:
                self.logger.error('%s already exists and exist_mode is set to exclusive, '
                                  'will stop to prevent accidentally overriding data' % self.data_path)
                raise FileExistsError

    def get_query_handler(self):
        """Get a *readable* index handler when the ``data_path`` already exist, need to be overrided
        """
        raise NotImplementedError

    def get_add_handler(self):
        """Get a *writable* index handler when the ``data_path`` already exist, need to be overrided"""
        raise NotImplementedError

    def get_create_handler(self):
        """Get a *writable* index handler when the ``data_path`` does not exist, need to be overrided"""
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
        call_obj_fn(self.add_handler, 'close')
        call_obj_fn(self.query_handler, 'close')
        super().close()

    def flush(self):
        """Flush all buffered data to ``data_path`` """
        call_obj_fn(self.add_handler, 'flush')
