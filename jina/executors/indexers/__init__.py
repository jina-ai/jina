__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
from typing import Tuple

import numpy as np

from .. import BaseExecutor
from ..compound import CompoundExecutor
from ...helper import call_obj_fn, cached_property


class BaseIndexer(BaseExecutor):
    """``BaseIndexer`` stores and searches with vectors.

    The key functions here are :func:`add` and :func:`query`.
    One can decorate them with :func:`jina.decorator.require_train`,
    :func:`jina.helper.batching` and :func:`jina.logging.profile.profiling`.

    One should always inherit from either :class:`BaseVectorIndexer` or :class:`BaseKVIndexer`.

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
                 index_filename: str = None,
                 *args, **kwargs):
        """

        :param index_filename: the name of the file for storing the index, when not given metas.name is used.
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.index_filename = index_filename  #: the file name of the stored index, no path is required
        self._size = 0

    def add(self, keys: 'np.ndarray', vectors: 'np.ndarray', *args, **kwargs):
        """Add new chunks and their vector representations

        :param keys: ``chunk_id`` in 1D-ndarray, shape B x 1
        :param vectors: vector representations in B x D
        """
        raise NotImplementedError

    def _validate_key_vector_shapes(self, keys, vectors):
        if len(vectors.shape) != 2:
            raise ValueError(f'vectors shape {vectors.shape} is not valid, expecting "vectors" to have rank of 2')

        if not getattr(self, 'num_dim', None):
            self.num_dim = vectors.shape[1]
            self.dtype = vectors.dtype.name
        elif self.num_dim != vectors.shape[1]:
            raise ValueError(
                f'vectors shape {vectors.shape} does not match with indexers\'s dim: {self.num_dim}')
        elif self.dtype != vectors.dtype.name:
            raise TypeError(
                f'vectors\' dtype {vectors.dtype.name} does not match with indexers\'s dtype: {self.dtype}')
        elif keys.shape[0] != vectors.shape[0]:
            raise ValueError(f'number of key {keys.shape[0]} not equal to number of vectors {vectors.shape[0]}')
        elif self.key_dtype != keys.dtype.name:
            raise TypeError(
                f'keys\' dtype {keys.dtype.name} does not match with indexers keys\'s dtype: {self.key_dtype}')

    def post_init(self):
        """query handler and write handler can not be serialized, thus they must be put into :func:`post_init`. """
        self.index_filename = self.index_filename or self.name
        self._query_handler = None
        self._write_handler = None

    def query(self, keys: 'np.ndarray', top_k: int, *args, **kwargs) -> Tuple['np.ndarray', 'np.ndarray']:
        """Find k-NN using query vectors, return chunk ids and chunk scores

        :param keys: query vectors in ndarray, shape B x D
        :param top_k: int, the number of nearest neighbour to return
        :return: a tuple of two ndarray.
            The first is ids in shape B x K (`dtype=int`), the second is scores in shape B x K (`dtype=float`)
        """
        raise NotImplementedError

    @property
    def index_abspath(self) -> str:
        """Get the file path of the index storage

        """
        return self.get_file_from_workspace(self.index_filename)

    @cached_property
    def query_handler(self):
        """A readable and indexable object, could be dict, map, list, numpy array etc. """
        if self._query_handler is None and os.path.exists(self.index_abspath):
            self._query_handler = self.get_query_handler()
            self.logger.info(f'indexer size: {self.size}')

        if self._query_handler is None:
            self.logger.warning(f'you can not query from {self} as its "query_handler" is not set. '
                                'If you are indexing data from scratch then it is fine. '
                                'If you are querying data then the index file must be empty or broken.')
        return self._query_handler

    @cached_property
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
        self.logger.info(f'indexer size: {self.size}')
        self.flush()
        call_obj_fn(self._write_handler, 'close')
        call_obj_fn(self._query_handler, 'close')
        super().close()

    def flush(self):
        """Flush all buffered data to ``index_abspath`` """
        call_obj_fn(self._write_handler, 'flush')


class BaseVectorIndexer(BaseIndexer):
    """An abstract class for vector indexer. It is equipped with drivers in ``requests.on``

    All vector indexers should inherit from it.

    It can be used to tell whether an indexer is vector indexer, via ``isinstance(a, BaseVectorIndexer)``
    """

    def query_by_id(self, ids: 'np.ndarray', *args, **kwargs):
        """ Get the vectors by id, return a subset of indexed vectors

        :param ids: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError


class BaseKVIndexer(BaseIndexer):
    """An abstract class for key-value indexer.

    All key-value indexers should inherit from it.

    It can be used to tell whether an indexer is key-value indexer, via ``isinstance(a, BaseKVIndexer)``
    """


class CompoundIndexer(CompoundExecutor):
    """A Frequently used pattern for combining A :class:`BaseVectorIndexer` and :class:`BaseKVIndexer`.
    It will be equipped with predefined ``requests.on`` behaviors:

        -  In the index time
            - 1. stores the vector via :class:`BaseVectorIndexer`
            - 2. remove all vector information (embedding, buffer, blob, text)
            - 3. store the remained meta information via :class:`BaseKVIndexer`
        - In the query time
            - 1. Find the knn using the vector via :class:`BaseVectorIndexer`
            - 2. remove all vector information (embedding, buffer, blob, text)
            - 3. Fill in the meta information of the chunk via :class:`BaseKVIndexer`

    One can use the :class:`ChunkIndexer` via

    .. highlight:: yaml
    .. code-block:: yaml

        !ChunkIndexer
        components:
          - !NumpyIndexer
            with:
              index_filename: vec.gz
            metas:
              name: vecidx  # a customized name
              workspace: $TEST_WORKDIR
          - !BasePbIndexer
            with:
              index_filename: chunk.gz
            metas:
              name: chunkidx  # a customized name
              workspace: $TEST_WORKDIR
        metas:
          name: chunk_compound_indexer
          workspace: $TEST_WORKDIR

    Without defining any ``requests.on`` logic. When load from this YAML, it will be auto equipped with

    .. highlight:: yaml
    .. code-block:: yaml

        on:
          SearchRequest:
            - !VectorSearchDriver
              with:
                executor: BaseVectorIndexer
            - !PruneDriver
              with:
                level: chunk
                pruned:
                  - embedding
                  - buffer
                  - blob
                  - text
            - !KVSearchDriver
              with:
                executor: BaseKVIndexer
                level: chunk
          IndexRequest:
            - !VectorIndexDriver
              with:
                executor: BaseVectorIndexer
            - !PruneDriver
              with:
                level: chunk
                pruned:
                  - embedding
                  - buffer
                  - blob
                  - text
            - !KVIndexDriver
              with:
                level: chunk
                executor: BaseKVIndexer
          ControlRequest:
            - !ControlReqDriver {}
    """
