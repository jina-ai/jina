__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import json
from typing import Union

from google.protobuf.json_format import Parse
from jina.executors.indexers.keyvalue.proto import BasePbIndexer
from jina.executors.indexers.keyvalue.proto import jina_pb2


class LeveldbIndexer(BasePbIndexer):
    """
    :class:`LeveldbIndexer` use `LevelDB` to save and query protobuf chunk/document.
    """

    def post_init(self):
        super().post_init()
        self._db_handler = None

    @property
    def db_handler(self):
        if self._db_handler is None:
            import plyvel
            self._db_handler = plyvel.DB(self.index_abspath, create_if_missing=True)
        return self._db_handler

    def get_add_handler(self):
        """Get the database handler

        """
        return self.db_handler

    def get_create_handler(self):
        """Get the database handler

        """
        return self.db_handler

    def add(self, objs):
        """Add a JSON-friendly object to the indexer

        :param objs: objects can be serialized into JSON format
        """
        with self.write_handler.write_batch() as h:
            for k, obj in objs.items():
                key = k.encode('utf8')
                value = json.dumps(obj).encode('utf8')
                h.put(key, value)

    def get_query_handler(self):
        """Get the database handler

        """
        return self.db_handler

    def query(self, key: str, *args, **kwargs) -> Union['jina_pb2.Chunk', 'jina_pb2.Document']:
        """Find the protobuf chunk/doc using id

        :param key: ``chunk_id`` or ``doc_id``
        :return: protobuf chunk or protobuf document
        """
        v = self.query_handler.get(key.encode('utf8'))
        value = None
        if v is not None:
            _parser = jina_pb2.Chunk if key[0] == 'c' else jina_pb2.Document
            value = Parse(json.loads(v.decode('utf8')), _parser())
        return value

    def close(self):
        """Close the database handler

        """
        super().close()
        self.write_handler.close()


class ChunkLeveldbIndexer(LeveldbIndexer):
    """"""


class DocLeveldbIndexer(LeveldbIndexer):
    """"""
