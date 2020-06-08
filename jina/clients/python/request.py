__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import ctypes
import mimetypes
import os
import random
import urllib.parse
from typing import Iterator, Union, Tuple, List

import numpy as np

from ...drivers.helper import array2pb, guess_mime
from ...enums import ClientMode
from ...helper import batch_iterator
from ...logging import default_logger
from ...proto import jina_pb2


def _generate(data: Union[Iterator[bytes], Iterator['jina_pb2.Document'], Iterator[str]], batch_size: int = 0,
              first_doc_id: int = 0, first_request_id: int = 0,
              random_doc_id: bool = False, mode: ClientMode = ClientMode.INDEX, top_k: int = 50,
              mime_type: str = None, filter_by: Union[Tuple[str], List[str], str] = None,
              *args, **kwargs) -> Iterator['jina_pb2.Message']:
    buffer_sniff = False

    try:
        import magic
        buffer_sniff = True
    except (ImportError, ModuleNotFoundError):
        default_logger.warning(f'can not sniff the MIME type '
                               f'MIME sniffing requires pip install "jina[http]" '
                               f'and brew install libmagic (Mac)/ apt-get install libmagic1 (Linux)')

    if mime_type and (mime_type not in mimetypes.types_map.values()):
        mime_type = mimetypes.guess_type(f'*.{mime_type}')[0]

    if isinstance(mode, str):
        mode = ClientMode.from_string(mode)

    for pi in batch_iterator(data, batch_size):
        req = jina_pb2.Request()
        req.request_id = first_request_id

        if mode == ClientMode.SEARCH:
            if top_k <= 0:
                raise ValueError('"top_k: %d" is not a valid number' % top_k)
            else:
                req.search.top_k = top_k

            if filter_by:
                if isinstance(filter_by, str):
                    filter_by = [filter_by]
                req.search.filter_by.extend(filter_by)

        for _raw in pi:
            d = getattr(req, str(mode).lower()).docs.add()
            if isinstance(_raw, jina_pb2.Document):
                d.CopyFrom(_raw)
            elif isinstance(_raw, np.ndarray):
                d.blob.CopyFrom(array2pb(_raw))
            elif isinstance(_raw, bytes):
                d.buffer = _raw
                if not mime_type and buffer_sniff:
                    try:
                        import magic
                        mime_type = magic.from_buffer(_raw, mime=True)
                    except Exception as ex:
                        default_logger.warning(f'can not sniff the MIME type due to the exception {ex}')
            elif isinstance(_raw, str):
                scheme = urllib.parse.urlparse(_raw).scheme
                if (scheme in {'http', 'https', 'data'} or os.path.exists(_raw)
                        or os.access(os.path.dirname(_raw), os.W_OK)):
                    d.uri = _raw
                    mime_type = guess_mime(_raw)
                else:
                    d.text = _raw
                    mime_type = 'text/plain'
            else:
                raise TypeError(f'{type(_raw)} type of input is not supported')

            if mime_type:
                d.mime_type = mime_type

            d.doc_id = first_doc_id if not random_doc_id else random.randint(0, ctypes.c_uint(-1).value)
            d.weight = 1.0
            first_doc_id += 1
        yield req
        first_request_id += 1


def index(*args, **kwargs):
    """Generate a indexing request"""
    yield from _generate(*args, **kwargs)


def train(*args, **kwargs):
    """Generate a training request """
    yield from _generate(*args, **kwargs)
    req = jina_pb2.Request()
    req.request_id = 1
    req.train.flush = True
    yield req


def search(*args, **kwargs):
    """Generate a searching request """
    yield from _generate(*args, **kwargs)
