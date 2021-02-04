__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
from typing import Tuple, List, Optional, Any, Iterable

import numpy as np

from .. import BaseExecutor
from ..compound import CompoundExecutor
from ...helper import call_obj_fn, cached_property, get_readable_size


class BaseIndexer(BaseExecutor):
    """Base class for storing and searching any kind of data structure.

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
        self._key_length = 16  #: the default minimum length of the key, will be expanded one time on the first batch

    @property
    def key_length(self) -> int:
        return self._key_length

    @key_length.setter
    def key_length(self, val: int):
        """Set the max key length. """
        if not self._key_length or self._key_length < val:
            # expand once
            self._key_length = val
        elif val < self._key_length:
            # just padding, no big deal
            self.logger.warning(
                f'key padding is triggered. this indexer allows only keys at length {self._key_length}, '
                f'but your max key length is {val}.')
        elif val > self._key_length:
            # panic
            raise ValueError(f'this indexer allows only keys at length {self._key_length}, but yours is {val}')

    def add(self, *args, **kwargs):
        """Add documents to the index.
        """
        raise NotImplementedError

    def update(self, *args, **kwargs):
        """Update documents on the index.
        """
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        """Delete documents from the index.
        """
        raise NotImplementedError

    def post_init(self):
        """query handler and write handler can not be serialized, thus they must be put into :func:`post_init`. """
        self.index_filename = self.index_filename or self.name
        self.handler_mutex = True  #: only one handler at a time by default
        self.is_handler_loaded = False

    def query(self, *args, **kwargs):
        """Query documents from the index.
        """
        raise NotImplementedError

    @property
    def index_abspath(self) -> str:
        """Get the file path of the index storage

        """
        return self.get_file_from_workspace(self.index_filename)

    @cached_property
    def query_handler(self):
        """A readable and indexable object, could be dict, map, list, numpy array etc.

        .. note::
            :attr:`query_handler` and :attr:`write_handler` are by default mutex
        """
        r = None
        if not self.handler_mutex or not self.is_handler_loaded:
            r = self.get_query_handler()
            if r is None:
                self.logger.warning(f'you can not query from {self} as its "query_handler" is not set. '
                                    'If you are indexing data from scratch then it is fine. '
                                    'If you are querying data then the index file must be empty or broken.')
            else:
                self.logger.info(f'indexer size: {self.size}')
                self.is_handler_loaded = True
        if r is None:
            r = self.null_query_handler
        return r

    @cached_property
    def null_query_handler(self) -> Optional[Any]:
        """The empty query handler when :meth:`get_query_handler` fails"""
        return

    @property
    def is_exist(self) -> bool:
        """Check if the database is exist or not"""
        return os.path.exists(self.index_abspath)

    @cached_property
    def write_handler(self):
        """A writable and indexable object, could be dict, map, list, numpy array etc.

        .. note::
            :attr:`query_handler` and :attr:`write_handler` are by default mutex
        """

        # ! a || ( a && b )
        # =
        # ! a || b
        if not self.handler_mutex or not self.is_handler_loaded:
            r = self.get_add_handler() if self.is_exist else self.get_create_handler()

            if r is None:
                self.logger.warning('"write_handler" is None, you may not add data to this index, '
                                    'unless "write_handler" is later assigned with a meaningful value')
            else:
                self.is_handler_loaded = True
            return r

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
        """The number of vectors or documents indexed """
        return self._size

    def __getstate__(self):
        d = super().__getstate__()
        self.flush()
        return d

    def close(self):
        """Close all file-handlers and release all resources. """
        self.logger.info(f'indexer size: {self.size} physical size: {get_readable_size(self.physical_size)}')
        self.flush()
        call_obj_fn(self.write_handler, 'close')
        call_obj_fn(self.query_handler, 'close')
        super().close()

    def flush(self):
        """Flush all buffered data to ``index_abspath`` """
        try:
            # It may have already been closed by the Pea using context manager
            call_obj_fn(self.write_handler, 'flush')
        except:
            pass

    def _filter_nonexistent_keys_values(self, keys: Iterable, values: Iterable, existent_keys: Iterable,
                                        check_path: str) -> Tuple[List, List]:
        keys = list(keys)
        values = list(values)
        if len(keys) != len(values):
            raise ValueError(f'Keys of length {len(keys)} did not match values of lenth {len(values)}')
        indices_to_drop = self._get_indices_to_drop(keys, existent_keys, check_path)
        keys = [keys[i] for i in range(len(keys)) if i not in indices_to_drop]
        values = [values[i] for i in range(len(values)) if i not in indices_to_drop]
        return keys, values

    def _filter_nonexistent_keys(self, keys: Iterable, existent_keys: Iterable, check_path: str) -> List:
        keys = list(keys)
        indices_to_drop = self._get_indices_to_drop(keys, existent_keys, check_path)
        keys = [keys[i] for i in range(len(keys)) if i not in indices_to_drop]
        return keys

    def _get_indices_to_drop(self, keys: List, existent_keys: Iterable, check_path: str):
        indices_to_drop = []
        for key_index, key in enumerate(keys):
            if key not in existent_keys:
                indices_to_drop.append(key_index)
        if indices_to_drop:
            self.logger.warning(
                f'Key(s) {[keys[i] for i in indices_to_drop]} were not found in {check_path}. Continuing anyway...')
        return indices_to_drop


class BaseVectorIndexer(BaseIndexer):
    """An abstract class for vector indexer. It is equipped with drivers in ``requests.on``

    All vector indexers should inherit from it.

    It can be used to tell whether an indexer is vector indexer, via ``isinstance(a, BaseVectorIndexer)``
    """

    def query_by_key(self, keys: Iterable[str], *args, **kwargs) -> 'np.ndarray':
        """ Get the vectors by id, return a subset of indexed vectors

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        :return: subset of indexed vectors
        """
        raise NotImplementedError

    def add(self, keys: Iterable[str], vectors: 'np.ndarray', *args, **kwargs):
        """Add new chunks and their vector representations

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param vectors: vector representations in B x D
        """
        raise NotImplementedError

    def query(self, query_vectors: 'np.ndarray', top_k: int, *args, **kwargs) -> Tuple['np.ndarray', 'np.ndarray']:
        """Find k-NN using query vectors, return chunk ids and chunk scores

        :param query_vectors: query vectors in ndarray, shape B x D
        :param top_k: int, the number of nearest neighbour to return
        :return: a tuple of two ndarray.
            The first is ids in shape B x K (`dtype=int`), the second is scores in shape B x K (`dtype=float`)
        """
        raise NotImplementedError

    def update(self, keys: Iterable[str], values: Iterable[bytes], *args, **kwargs):
        """Update vectors on the index.

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param values: vector representations in B x D
        """
        raise NotImplementedError

    def delete(self, keys: Iterable[str], *args, **kwargs):
        """Delete vectors from the index.

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        """
        raise NotImplementedError


class BaseKVIndexer(BaseIndexer):
    """An abstract class for key-value indexer.

    All key-value indexers should inherit from it.

    It can be used to tell whether an indexer is key-value indexer, via ``isinstance(a, BaseKVIndexer)``
    """

    def add(self, keys: Iterable[str], values: Iterable[bytes], *args, **kwargs):
        """Add the serialized documents to the index via document ids.

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param values: serialized documents
        """
        raise NotImplementedError

    def query(self, key: Any) -> Optional[Any]:
        """Find the serialized document to the index via document id.

        :param key: document id
        :return: serialized documents
        """
        raise NotImplementedError

    def update(self, keys: Iterable[str], values: Iterable[bytes], *args, **kwargs):
        """Update the serialized documents on the index via document ids.

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        :param values: serialized documents
        """
        raise NotImplementedError

    def delete(self, keys: Iterable[str], *args, **kwargs):
        """Delete the serialized documents from the index via document ids.

        :param keys: a list of ``id``, i.e. ``doc.id`` in protobuf
        """
        raise NotImplementedError

    def __getitem__(self, key: Any) -> Optional[Any]:
        return self.query(key)


class UniqueVectorIndexer(CompoundExecutor):
    """A frequently used pattern for combining a :class:`BaseVectorIndexer` and a :class:`DocCache` """


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
            - 3. Fill in the meta information of the document via :class:`BaseKVIndexer`

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
              workspace: ${{TEST_WORKDIR}}
          - !BinaryPbIndexer
            with:
              index_filename: chunk.gz
            metas:
              name: chunkidx  # a customized name
              workspace: ${{TEST_WORKDIR}}
        metas:
          name: chunk_compound_indexer
          workspace: ${{TEST_WORKDIR}}

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
                pruned:
                  - embedding
                  - buffer
                  - blob
                  - text
            - !KVSearchDriver
              with:
                executor: BaseKVIndexer
            IndexRequest:
            - !VectorIndexDriver
              with:
                executor: BaseVectorIndexer
            - !PruneDriver
              with:
                pruned:
                  - embedding
                  - buffer
                  - blob
                  - text
            - !KVIndexDriver
              with:
                executor: BaseKVIndexer
          ControlRequest:
            - !ControlReqDriver {}
    """
