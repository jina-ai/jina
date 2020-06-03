__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import gzip
import json
from typing import Union

from google.protobuf.json_format import Parse

from jina.executors.indexers import BaseKVIndexer
from jina.proto import jina_pb2


class BasePbIndexer(BaseKVIndexer):
    """Storing and querying protobuf chunk/document using gzip and Python dict. """

    compress_level = 1  #: The compresslevel argument is an integer from 0 to 9 controlling the level of compression
    flush_on_add = True  #: When set to true, the indexer is flushed on every add, it is safer but slower

    def get_query_handler(self):
        r = {}
        with gzip.open(self.index_abspath, 'rt') as fp:
            for l in fp:
                if l:
                    tmp = json.loads(l)
                    for k, v in tmp.items():
                        _parser = jina_pb2.Chunk if k[0] == 'c' else jina_pb2.Document
                        r[k] = Parse(v, _parser())
        return r

    def get_add_handler(self):
        """Append to the existing gzip file using text appending mode """

        # note this write mode must be append, otherwise the index will be overwrite in the search time
        return gzip.open(self.index_abspath, 'at', compresslevel=self.compress_level)

    def get_create_handler(self):
        """Create a new gzip file

        :return: a gzip file stream
        """
        return gzip.open(self.index_abspath, 'wt', compresslevel=self.compress_level)

    def add(self, obj):
        """Add a JSON-friendly object to the indexer

        :param obj: an object can be jsonified
        """
        json.dump(obj, self.write_handler)
        self.write_handler.write('\n')
        if self.flush_on_add:
            self.flush()

    def query(self, key: int) -> Union['jina_pb2.Chunk', 'jina_pb2.Document']:
        """ Find the protobuf chunk/doc using id

        :param key: ``chunk_id`` or ``doc_id``
        :return: protobuf chunk or protobuf document
        """
        if self.query_handler is not None and key in self.query_handler:
            return self.query_handler[key]


class ChunkPbIndexer(BasePbIndexer):
    """Shortcut for :class:`BasePbIndexer` equipped with ``requests.on`` for storing chunk-level protobuf info,
     differ with :class:`DocPbIndexer` in ``requests.on`` """


class DocPbIndexer(BasePbIndexer):
    """Shortcut for :class:`BasePbIndexer` equipped with ``requests.on`` for storing doc-level protobuf info,
    differ with :class:`ChunkPbIndexer` only in ``requests.on`` """


class DataURIPbIndexer(DocPbIndexer):
    """Shortcut for :class:`DocPbIndexer` equipped with ``requests.on`` for storing doc-level protobuf and data uri info,
    differ with :class:`ChunkPbIndexer` only in ``requests.on`` """
