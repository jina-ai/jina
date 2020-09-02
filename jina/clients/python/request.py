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

if False:
    from ...counter import BaseCounter


def _add_document(request: 'jina_pb2.Request', content: Union['jina_pb2.Document', 'np.ndarray', bytes, str], mode: str,
                  doc_counter: 'BaseCounter', docs_in_same_batch: int, mime_type: str, buffer_sniff: bool,
                  granularity: int):
    d = getattr(request, str(mode).lower()).docs.add()
    if isinstance(content, jina_pb2.Document):
        d.CopyFrom(content)
    elif isinstance(content, np.ndarray):
        d.blob.CopyFrom(array2pb(content))
    elif isinstance(content, bytes):
        d.buffer = content
        if not mime_type and buffer_sniff:
            try:
                import magic
                mime_type = magic.from_buffer(content, mime=True)
            except Exception as ex:
                default_logger.warning(f'can not sniff the MIME type due to the exception {ex}')
    elif isinstance(content, str):
        scheme = urllib.parse.urlparse(content).scheme
        if ((scheme in {'http', 'https'} and is_url(content)) or (scheme in {'data'}) or os.path.exists(content)
                or os.access(os.path.dirname(content), os.W_OK)):
            d.uri = content
            mime_type = guess_mime(content)
        else:
            d.text = content
            mime_type = 'text/plain'
    else:
        raise TypeError(f'{type(content)} type of input is not supported')

    if mime_type:
        d.mime_type = mime_type

    d.id = next(doc_counter)
    d.weight = 1.0
    d.length = docs_in_same_batch
    d.granularity = granularity


def _generate(data: Union[Iterator['jina_pb2.Document'], Iterator[bytes], Iterator['np.ndarray'], Iterator[str], 'np.ndarray'],
              batch_size: int = 0, first_doc_id: int = 0, first_request_id: int = 0,
              random_doc_id: bool = False, mode: ClientMode = ClientMode.INDEX,
              mime_type: str = None, queryset: Iterator['jina_pb2.QueryLang'] = None,
              granularity: int = 0, *args, **kwargs) -> Iterator['jina_pb2.Message']:
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

    for batch in batch_iterator(data, batch_size):
        req = jina_pb2.Request()
        req.request_id = next(req_counter)
        if queryset:
            if isinstance(queryset, jina_pb2.QueryLang):
                queryset = [queryset]
            req.queryset.extend(queryset)

        for content in batch:
            _add_document(request=req, content=content, mode=mode, doc_counter=doc_counter,
                          docs_in_same_batch=batch_size, mime_type=mime_type,
                          buffer_sniff=buffer_sniff, granularity=granularity)
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
