__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import gzip
import json
from typing import Union, Iterator

from google.protobuf.json_format import Parse

from .... import __binary_delimiter__
from ....executors.indexers import BaseKVIndexer
from ....proto import jina_pb2


class BasePbIndexer(BaseKVIndexer):
    """Storing and querying protobuf chunk/document using gzip and Python dict. """

    compress_level = 1  #: The compresslevel argument is an integer from 0 to 9 controlling the level of compression
    flush_on_add = True  #: When set to true, the indexer is flushed on every add, it is safer but slower
    mode = 't'  #: r/w mode, `t` for text, `b` for binary

    def __init__(self, index_filename: str, level: str, *args, **kwargs):
        super().__init__(index_filename, *args, **kwargs)
        self.level = level

    def post_init(self):
        if self.level == 'chunk':
            self._parser = jina_pb2.Chunk
        elif self.level == 'doc':
            self._parser = jina_pb2.Document
        else:
            raise NotImplementedError(f'{self.level} is not supported!')
        super().post_init()

    def get_add_handler(self):
        """Append to the existing gzip file using text appending mode """

        # note this write mode must be append, otherwise the index will be overwrite in the search time
        return gzip.open(self.index_abspath, 'a' + self.mode, compresslevel=self.compress_level)

    def get_create_handler(self):
        """Create a new gzip file

        :return: a gzip file stream
        """
        return gzip.open(self.index_abspath, 'w' + self.mode, compresslevel=self.compress_level)

    def query(self, key: int) -> Union['jina_pb2.Chunk', 'jina_pb2.Document']:
        """ Find the protobuf chunk/doc using id

        :param key: ``chunk_id`` or ``doc_id``
        :return: protobuf chunk or protobuf document
        """
        if self.query_handler is not None and key in self.query_handler:
            return self.query_handler[key]

    def get_query_handler(self):
        raise NotImplementedError

    def add(self, *args, **kwargs):
        self._add(*args, **kwargs)
        if self.flush_on_add:
            self.flush()

    def _add(self, *args, **kwargs):
        raise NotImplementedError


class JsonPbIndexer(BasePbIndexer):
    """Storing and querying protobuf chunk/document in JSON using gzip and Python dict. """

    def get_query_handler(self):
        r = {}
        with gzip.open(self.index_abspath, 'rt') as fp:
            for l in fp:
                if l:
                    tmp = json.loads(l)
                    for k, v in tmp.items():
                        r[k] = Parse(v, self._parser())
                        self._size += 1
        return r

    def _add(self, keys: Iterator[Union['jina_pb2.Chunk', 'jina_pb2.Document']], *args, **kwargs):
        """Add a JSON-friendly object to the indexer

        :param obj: an object can be jsonified
        """
        if self.level == 'chunk':
            keys = {k.chunk_id: k for k in keys}
        elif self.level == 'doc':
            keys = {k.doc_id: k for k in keys}
        else:
            raise NotImplementedError
        json.dump(keys, self.write_handler)
        self._size += len(keys)
        self.write_handler.write('\n')


class BinaryPbIndexer(BasePbIndexer):
    """Storing and querying protobuf chunk/document in binary using gzip and Python dict.

    .. note::
        it often yields better performance than :class:`JsonPbIndexer`
    """

    mode = 'b'

    def get_query_handler(self):
        with gzip.open(self.index_abspath, 'rb') as fp:
            tmp = fp.read()
        if tmp.endswith(__binary_delimiter__):
            tmp = tmp[:-len(__binary_delimiter__)]

        r = {}
        for l in tmp.split(__binary_delimiter__):
            b = self._parser()
            b.ParseFromString(l)
            if self.level == 'chunk':
                r[b.chunk_id] = b
                self._size += 1
            elif self.level == 'doc':
                r[b.doc_id] = b
                self._size += 1
        return r

    def _add(self, keys: Iterator[Union['jina_pb2.Chunk', 'jina_pb2.Document']], *args, **kwargs):
        """Add a object to the indexer

        :param obj: an object
        """
        for k in keys:
            self.write_handler.write(k.SerializeToString() + __binary_delimiter__)
            self._size += 1


class ChunkPbIndexer(BinaryPbIndexer):
    """Shortcut for :class:`BasePbIndexer` equipped with ``requests.on`` for storing chunk-level protobuf info,
     differ with :class:`DocPbIndexer` in ``requests.on`` """

    def __init__(self, index_filename: str, level: str = 'chunk', *args, **kwargs):
        super().__init__(index_filename, level, *args, **kwargs)


class DocPbIndexer(BinaryPbIndexer):
    """Shortcut for :class:`BasePbIndexer` equipped with ``requests.on`` for storing doc-level protobuf info,
    differ with :class:`ChunkPbIndexer` only in ``requests.on`` """

    def __init__(self, index_filename: str, level: str = 'doc', *args, **kwargs):
        super().__init__(index_filename, level, *args, **kwargs)


class DataURIPbIndexer(DocPbIndexer):
    """Shortcut for :class:`DocPbIndexer` equipped with ``requests.on`` for storing doc-level protobuf and data uri info,
    differ with :class:`ChunkPbIndexer` only in ``requests.on`` """
