import mmap
import os
import time
from typing import Optional, Union

import numpy as np

from jina.executors.indexers import BaseKVIndexer
from jina.executors.indexers.keyvalue import BinaryPbIndexer
from jina.executors.indexers.query import QueryReloadIndexer
from jina.executors.indexers.vector import BaseNumpyIndexer
from jina.executors.dump import DumpPersistor

HEADER_NONE_ENTRY = (-1, -1, -1)
TIME_WAIT_SWITCH = 5


class QueryBinaryPbIndexer(BinaryPbIndexer, QueryReloadIndexer):
    """Simple Key-value indexer."""

    def __init__(self, uri_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uri_path = uri_path
        self.preparing = False
        if self.uri_path:
            self.import_uri_path(self.uri_path)
        else:
            self.logger.warning(
                f'The indexer does not have any data. Make sure to use ReloadRequest to tell it how to import data...'
            )

    def import_uri_path(self, path):
        """This can be a universal dump format(to be defined)
        Or optimized to the Indexer format.

        We first copy to a temporary folder (within workspace?)

        The dump is created by a DumpRequest to the CUD Indexer (SQLIndexer)
        with params:
            formats: universal, Numpy, BinaryPb etc.
            shards: X

        The shards are configured per dump
        """
        print(f'### QBP Importing from dump at {path}')
        ids, metas = DumpPersistor.import_metas(path)
        self.add(list(ids), list(metas))
        self.write_handler.flush()
        self.write_handler.close()
        self.handler_mutex = False
        self.is_handler_loaded = False
        # warming up
        self.query('someid')
        print(f'### QBP self.size after import: {self.size}')
