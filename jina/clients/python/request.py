__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import mimetypes
import os
import urllib.parse
from typing import Iterator, Union

import numpy as np

from ...counter import RandomUintCounter, SimpleCounter
from ...drivers.helper import array2pb, guess_mime
from ...enums import ClientMode
from ...helper import batch_iterator, is_url
from ...logging import default_logger
from ...proto import jina_pb2


def _generate(data: Union[Iterator[bytes], Iterator['jina_pb2.Document'], Iterator[str]], batch_size: int = 0,
              first_doc_id: int = 0, first_request_id: int = 0,
              random_doc_id: bool = False, mode: ClientMode = ClientMode.INDEX,
              mime_type: str = None, queryset: Iterator['jina_pb2.QueryLang'] = None,
              *args, **kwargs) -> Iterator['jina_pb2.Message']:
    buffer_sniff = False
    doc_counter = RandomUintCounter() if random_doc_id else SimpleCounter(first_doc_id)
    req_counter = SimpleCounter(first_request_id)

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
        req.request_id = next(req_counter)
        if queryset:
            if isinstance(queryset, jina_pb2.QueryLang):
                queryset = [queryset]
            req.queryset.extend(queryset)

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
                if ((scheme in {'http', 'https'} and is_url(_raw)) or (scheme in {'data'}) or os.path.exists(_raw)
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

            d.id = next(doc_counter)
            d.weight = 1.0
            d.length = batch_size
        yield req


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
