import mmap
import os
import pickle
import shutil
from typing import List, Tuple, Generator, Optional, Iterable

import numpy as np

from ..dump import export_dump_streaming
from ..keyvalue import BinaryPbWriterMixin
from .... import Executor, requests, DocumentArray, Document
from ....helper import call_obj_fn, cached_property, get_readable_size
from ....logging import JinaLogger

HEADER_NONE_ENTRY = (-1, -1, -1)


class BinaryPbDBMSIndexer(Executor, BinaryPbWriterMixin):
    """
    A DBMS Indexer (no query method)

    :param index_filename: the name of the file for storing the index, when not given metas.name is used.
    :param key_length: the default minimum length of the key, will be expanded one time on the first batch
    :param args:  Additional positional arguments which are just used for the parent initialization
    :param kwargs: Additional keyword arguments which are just used for the parent initialization
    """

    def __init__(
        self,
        index_filename: Optional[str] = None,
        key_length: int = 36,
        dump_on_exit: str = True,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.index_filename = index_filename or self.metas.name

        self.key_length = key_length
        self._size = 0

        self.handler_mutex = True
        self.is_handler_loaded = False

        self._start = 0
        self._page_size = mmap.ALLOCATIONGRANULARITY
        self.logger = JinaLogger(self.__class__.__name__)
        self._dump_on_exit = dump_on_exit

    @cached_property
    def query_handler(self):
        """A readable and indexable object, could be dict, map, list, numpy array etc.

        :return: read handler

        .. note::
            :attr:`query_handler` and :attr:`write_handler` are by default mutex
        """
        r = None
        if not self.handler_mutex or not self.is_handler_loaded:
            r = self.get_query_handler()
            if r is None:
                self.logger.warning(
                    f'you can not query from {self} as its "query_handler" is not set. '
                    'If you are indexing data from scratch then it is fine. '
                    'If you are querying data then the index file must be empty or broken.'
                )
            else:
                self.logger.info(f'indexer size: {self.size}')
                self.is_handler_loaded = True
        return r

    @property
    def is_exist(self) -> bool:
        """
        Check if the database is exist or not

        :return: true if the absolute index path exists, else false
        """
        return os.path.exists(self.index_abspath)

    @cached_property
    def write_handler(self):
        """A writable and indexable object, could be dict, map, list, numpy array etc.

        :return: write handler

        .. note::
            :attr:`query_handler` and :attr:`write_handler` are by default mutex
        """

        # ! a || ( a && b )
        # =
        # ! a || b
        if not self.handler_mutex or not self.is_handler_loaded:
            r = self.get_add_handler() if self.is_exist else self.get_create_handler()

            if r is None:
                self.logger.warning(
                    '"write_handler" is None, you may not add data to this index, '
                    'unless "write_handler" is later assigned with a meaningful value'
                )
            else:
                self.is_handler_loaded = True
            return r

    @property
    def size(self) -> int:
        """
        The number of vectors or documents indexed.

        :return: size
        """
        return self._size

    def __getstate__(self):
        d = super().__getstate__()
        self.flush()
        return d

    @property
    def default_dump_path(self):
        return os.path.join(self.workspace, 'dump')

    def close(self):
        """Close all file-handlers and release all resources. """
        self.logger.info(
            f'indexer size: {self.size} physical size: {get_readable_size(physical_size(self.workspace))}'
        )
        self.flush()
        if self._dump_on_exit:
            shutil.rmtree(self.default_dump_path, ignore_errors=True)
            self.dump({'dump_path': self.default_dump_path})
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

    def _filter_nonexistent_keys_values(
        self, keys: Iterable, values: Iterable, existent_keys: Iterable
    ) -> Tuple[Iterable, Iterable]:
        f = [(key, value) for key, value in zip(keys, values) if key in existent_keys]
        if f:
            return zip(*f)
        else:
            return None, None

    def _filter_nonexistent_keys(
        self, keys: Iterable, existent_keys: Iterable
    ) -> Iterable:
        return [key for key in keys if key in set(existent_keys)]

    @property
    def index_abspath(self) -> str:
        """
        Get the file path of the index storage

        :return: absolute path
        """
        os.makedirs(self.workspace, exist_ok=True)
        return os.path.join(self.workspace, self.index_filename)

    def _get_generator(
        self, ids: List[str]
    ) -> Generator[Tuple[str, np.array, bytes], None, None]:
        for id_ in ids:
            vecs_metas_bytes = super()._query(id_)
            vec, meta = pickle.loads(vecs_metas_bytes)
            yield id_, vec, meta

    @requests(on='/dump')
    def dump(self, docs, parameters, **kwargs) -> None:
        """Dump the index

        :param parameters: requests parameters
        :param args: not used
        :param kwargs: not used
        """
        self.write_handler.close()
        # noinspection PyPropertyAccess
        del self.write_handler
        self.handler_mutex = False
        ids = self.query_handler.header.keys()
        export_dump_streaming(
            parameters['dump_path'],
            shards=parameters.get('shards', 1),
            size=len(ids),
            data=self._get_generator(ids),
        )
        self.query_handler.close()
        self.handler_mutex = False
        # noinspection PyPropertyAccess
        del self.query_handler

    @requests(on='/index')
    def add(self, docs: DocumentArray, *args, **kwargs):
        """Add to the DBMS Indexer, both vectors and metadata

        :param docs: `DocumentArray` of to-be-added Documents
        :param args: not used
        :param kwargs: not used
        """

        ids, vecs, metas = self._unpack_docs(docs)
        if not any(ids):
            return

        vecs_metas = [pickle.dumps((vec, meta)) for vec, meta in zip(vecs, metas)]
        with self.write_handler as write_handler:
            self._add(ids, vecs_metas, write_handler)

    @requests(on='/update')
    def update(self, docs: DocumentArray, *args, **kwargs):
        """Update the DBMS Indexer, both vectors and metadata

        :param docs: `DocumentArray` of to-be-updated Documents
        :param args: not used
        :param kwargs: not used
        """
        ids, vecs, metas = self._unpack_docs(docs)
        vecs_metas = [pickle.dumps((vec, meta)) for vec, meta in zip(vecs, metas)]
        keys, vecs_metas = self._filter_nonexistent_keys_values(
            ids, vecs_metas, self.query_handler.header.keys()
        )
        del self.query_handler
        self.handler_mutex = False
        if keys:
            self._delete(keys)
            with self.write_handler as write_handler:
                self._add(keys, vecs_metas, write_handler)

    def _unpack_docs(self, docs: DocumentArray, *args, **kwargs) -> None:
        info = [
            (
                doc.id,
                doc.embedding,
                BinaryPbDBMSIndexer._doc_without_embedding(doc).SerializeToString(),
            )
            for doc in docs
        ]
        if info:
            ids, vecs, metas = zip(*info)
            self.check_key_length(ids)
            return ids, vecs, metas

    @staticmethod
    def _doc_without_embedding(d):
        new_doc = Document(d, copy=True)
        new_doc.ClearField('embedding')
        return new_doc

    def check_key_length(self, val: Iterable[str]):
        """
        Check if the max length of val(e.g. doc id) is larger than key_length.

        :param val: The values to be checked
        """
        m_val = max(len(v) for v in val)
        if m_val > self.key_length:
            raise ValueError(
                f'BinaryPbDBMSIndexer allows only keys of length {self.key_length}, '
                f'but yours is {m_val}.'
            )
