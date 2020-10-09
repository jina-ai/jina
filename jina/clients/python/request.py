__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import mimetypes
import os
import urllib.parse
import uuid
from typing import Iterator, Union, Optional, Tuple

import numpy as np

from ...drivers.helper import array2pb, guess_mime
from ...enums import ClientMode
from ...helper import batch_iterator, is_url
from ...logging import default_logger
from ...proto import jina_pb2, uid


def _fill_document(document: 'jina_pb2.Document',
                   content: Union['jina_pb2.Document', 'np.ndarray', bytes, str, Tuple[
                       Union['jina_pb2.Document', bytes], Union['jina_pb2.Document', bytes]]],
                   docs_in_same_batch: int,
                   mime_type: str,
                   buffer_sniff: bool,
                   override_doc_id: bool = True
                   ):
    if isinstance(content, jina_pb2.Document):
        document.CopyFrom(content)
    elif isinstance(content, np.ndarray):
        document.blob.CopyFrom(array2pb(content))
    elif isinstance(content, bytes):
        document.buffer = content
        if not mime_type and buffer_sniff:
            try:
                import magic

                mime_type = magic.from_buffer(content, mime=True)
            except Exception as ex:
                default_logger.warning(
                    f'can not sniff the MIME type due to the exception {ex}'
                )
    elif isinstance(content, str):
        scheme = urllib.parse.urlparse(content).scheme
        if (
                (scheme in {'http', 'https'} and is_url(content))
                or (scheme in {'data'})
                or os.path.exists(content)
                or os.access(os.path.dirname(content), os.W_OK)
        ):
            document.uri = content
            mime_type = guess_mime(content)
        else:
            document.text = content
            mime_type = 'text/plain'
    else:
        raise TypeError(f'{type(content)} type of input is not supported')

    if mime_type:
        document.mime_type = mime_type

    # TODO: I don't like this part, this change the original docs inplace!
    #   why can't delegate this to crafter? (Han)
    document.weight = 1.0
    document.length = docs_in_same_batch

    if override_doc_id:
        document.id = uid.new_doc_id(document)


def _generate(data: Union[Iterator[Union['jina_pb2.Document', bytes]], Iterator[
    Tuple[Union['jina_pb2.Document', bytes], Union['jina_pb2.Document', bytes]]], Iterator['np.ndarray'], Iterator[
                              str], 'np.ndarray',],
              batch_size: int = 0, mode: ClientMode = ClientMode.INDEX,
              top_k: Optional[int] = None,
              mime_type: str = None,
              override_doc_id: bool = True,
              queryset: Iterator['jina_pb2.QueryLang'] = None,
              *args,
              **kwargs,
              ) -> Iterator['jina_pb2.Message']:

    buffer_sniff = False

    try:
        import magic

        buffer_sniff = True
    except (ImportError, ModuleNotFoundError):
        default_logger.warning(
            f'can not sniff the MIME type '
            f'MIME sniffing requires pip install "jina[http]" '
            f'and brew install libmagic (Mac)/ apt-get install libmagic1 (Linux)'
        )

    if mime_type and (mime_type not in mimetypes.types_map.values()):
        mime_type = mimetypes.guess_type(f'*.{mime_type}')[0]

    if isinstance(mode, str):
        mode = ClientMode.from_string(mode)

    for batch in batch_iterator(data, batch_size):
        req = jina_pb2.Request()
        req.request_id = uuid.uuid1().hex
        if queryset:
            if isinstance(queryset, jina_pb2.QueryLang):
                queryset = [queryset]
            req.queryset.extend(queryset)

        if top_k and mode == ClientMode.SEARCH:
            if top_k <= 0:
                raise ValueError(f'"top_k: {top_k}" is not a valid number')
            else:
                top_k_queryset = jina_pb2.QueryLang()
                top_k_queryset.name = 'VectorSearchDriver'
                top_k_queryset.priority = 1
                top_k_queryset.parameters['top_k'] = top_k
                req.queryset.extend([top_k_queryset])

        for content in batch:
            # TODO:
            if mode != ClientMode.EVALUATE:
                d = getattr(req, str(mode).lower()).docs.add()
                _fill_document(document=d,
                               content=content,
                               docs_in_same_batch=batch_size,
                               mime_type=mime_type,
                               buffer_sniff=buffer_sniff,
                               override_doc_id=override_doc_id
                               )
            else:
                assert len(content) == 2, 'You are passing an Evaluation Request without providing two parts (a ' \
                                          'document and its groundtruth) '
                d = getattr(req, str(mode).lower()).docs.add()
                _fill_document(document=d,
                               content=content[0],
                               docs_in_same_batch=batch_size,
                               mime_type=mime_type,
                               buffer_sniff=buffer_sniff,
                               override_doc_id=override_doc_id
                               )
                groundtruth = getattr(req, str(mode).lower()).groundtruths.add()
                _fill_document(document=groundtruth,
                               content=content[1],
                               docs_in_same_batch=batch_size,
                               mime_type=mime_type,
                               buffer_sniff=buffer_sniff,
                               override_doc_id=override_doc_id
                               )
        yield req


def index(*args, **kwargs):
    """Generate a indexing request"""
    yield from _generate(*args, **kwargs)


def train(*args, **kwargs):
    """Generate a training request """
    yield from _generate(*args, **kwargs)
    req = jina_pb2.Request()
    req.request_id = uuid.uuid1().hex
    req.train.flush = True
    yield req


def search(*args, **kwargs):
    """Generate a searching request """
    yield from _generate(*args, **kwargs)


def evaluate(*args, **kwargs):
    """Generate an evaluation request """
    yield from _generate(*args, **kwargs)
