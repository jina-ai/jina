__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
import struct
from typing import Iterable

from . import BaseRecursiveDriver
from ..proto import uid

if False:
    from ..proto import jina_pb2


class BloomFilterDriver(BaseRecursiveDriver):
    """ Bloom filter to test whether a doc is observed or not based on its ``doc.id``.
    It is used to speed up answers in a key-value storage system.
    Values are stored on a disk which has slow access times. Bloom filter decisions are much faster.
    """

    def __init__(self, bit_array: int = 0, num_hash: int = 8, *args, **kwargs):
        """

        :param bit_array: a bit array of m bits, all set to 0.
        :param num_hash: number of hash functions, can only be 4, 8.
            larger value, slower, but more memory efficient
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self._bit_array = bit_array
        # unpack int64 (8 bytes) to eight uint8 (1 bytes)
        # to simulate a group of hash functions in bloom filter
        if num_hash == 4:
            # 8 bytes/4 = 2 bytes = H (unsigned short)
            fmt = 'H' * 4
        elif num_hash == 8:
            fmt = 'B' * 8
        else:
            raise ValueError(f'"num_hash" must be 4 or 8 but given {num_hash}')
        self._hash_funcs = lambda x: struct.unpack(fmt, uid.id2bytes(x))

    def __contains__(self, doc_id: str):
        for _r in self._hash_funcs(doc_id):
            if not (self._bit_array & (1 << _r)):
                return False
        return True

    def on_hit(self, doc: 'jina_pb2.Document'):
        """Function to call when doc exists"""
        raise NotImplementedError

    def on_miss(self, doc: 'jina_pb2.Document'):
        """Function to call when doc is missing"""
        pass

    def _add(self, doc_id: str):
        for _r in self._hash_funcs(doc_id):
            self._bit_array |= (1 << _r)

    def _flush(self):
        """Write the bloom filter by writing ``_bit_array`` back"""
        pass

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs) -> None:
        for doc in docs:
            if doc.id in self:
                self.on_hit(doc)
            else:
                self._add(doc.id)
                self.on_miss(doc)
        self._flush()


class EnvBloomFilterDriver(BloomFilterDriver):
    """
    A :class:`BloomFilterDriver` that stores ``bit_array`` in OS environment.

    Just an example how to share & persist ``bit_array``

    """

    def __init__(self, env_name: str = 'JINA_BLOOMFILTER_1', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._env_name = env_name
        self._bit_array = int(os.environ.get(env_name, '0'), 2)

    def _flush(self):
        os.environ[self._env_name] = bin(self._bit_array)[2:]
