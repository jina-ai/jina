from typing import Optional, List

import numpy as np
from jina.executors.indexers import BaseIndexer


class BaseDBMSIndexer(BaseIndexer):
    """A class only meant for storing (indexing, update, delete) of data"""

    def add(
        self, ids: List[str], vecs: List[np.array], metas: List[bytes], *args, **kwargs
    ):
        """Add to the DBMS Indexer, both vectors and metadata

        :param ids: the ids of the documents
        :param vecs: the vectors
        :param metas: the metadata, in binary format
        :param args: not used
        :param kwargs: not used
        """
        raise NotImplementedError

    def update(
        self, ids: List[str], vecs: List[np.array], metas: List[bytes], *args, **kwargs
    ):
        """Update the DBMS Indexer, both vectors and metadata

        :param ids: the ids of the documents
        :param vecs: the vectors
        :param metas: the metadata, in binary format
        :param args: not used
        :param kwargs: not used
        """
        raise NotImplementedError

    def delete(self, ids: List[str], *args, **kwargs):
        """Delete from the indexer by ids

        :param ids: the ids of the Documents to delete
        :param args: not used
        :param kwargs: not used
        """
        raise NotImplementedError

    def dump(self, path: str, shards: int):
        """Dump the index

        :param path: the path to which to dump
        :param shards: the nr of shards to which to dump
        """
        raise NotImplementedError

    def query(self, key: str, *args, **kwargs) -> Optional[bytes]:
        """DBMSIndexers do NOT support querying

        :param key: the key by which to query
        :param args: not used
        :param kwargs: not used
        """
        raise NotImplementedError('DBMSIndexers do not support querying')
