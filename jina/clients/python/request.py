import ctypes
import random
from typing import Iterator

from ...helper import batch_iterator
from ...proto import jina_pb2


def _generate(data: Iterator[bytes], batch_size: int = 0,
              doc_id_start: int = 0, request_id_start: int = 0,
              random_doc_id: bool = False, mode: str = 'index', top_k: int = 50,
              *args, **kwargs) -> Iterator['jina_pb2.Message']:
    for pi in batch_iterator(data, batch_size):
        req = jina_pb2.Request()
        req.request_id = request_id_start

        if mode == 'search':
            if top_k <= 0:
                raise ValueError('"top_k: %d" is not a valid number' % top_k)
            else:
                req.search.top_k = top_k

        for raw_bytes in pi:
            d = getattr(req, mode).docs.add()
            d.doc_id = doc_id_start if not random_doc_id else random.randint(0, ctypes.c_uint(-1).value)
            d.raw_bytes = raw_bytes
            d.weight = 1.0
            doc_id_start += 1
        yield req
        request_id_start += 1


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
