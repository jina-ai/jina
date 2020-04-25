__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import ctypes
import random
from typing import Iterator, Union

from ...helper import batch_iterator
from ...proto import jina_pb2


def _generate(data: Union[Iterator[bytes], Iterator['jina_pb2.Document']], batch_size: int = 0,
              first_doc_id: int = 0, first_request_id: int = 0,
              random_doc_id: bool = False, mode: str = 'index', top_k: int = 50,
              in_proto: bool = False,
              *args, **kwargs) -> Iterator['jina_pb2.Message']:
    for pi in batch_iterator(data, batch_size):
        req = jina_pb2.Request()
        req.request_id = first_request_id

        if mode == 'search':
            if top_k <= 0:
                raise ValueError('"top_k: %d" is not a valid number' % top_k)
            else:
                req.search.top_k = top_k

        for raw_bytes in pi:
            d = getattr(req, mode).docs.add()
            if in_proto:
                d.CopyFrom(raw_bytes)
            else:
                d.raw_bytes = raw_bytes
            d.doc_id = first_doc_id if not random_doc_id else random.randint(0, ctypes.c_uint(-1).value)
            d.weight = 1.0
            first_doc_id += 1
        yield req
        first_request_id += 1


def index(*args, **kwargs):
    """Generate indexing request"""
    yield from _generate(*args, **kwargs)


def train(*args, **kwargs):
    """Generate training request """
    yield from _generate(*args, **kwargs)
    req = jina_pb2.Request()
    req.request_id = 1
    req.train.flush = True
    yield req


def search(*args, **kwargs):
    """Generate search request """
    yield from _generate(*args, **kwargs)
