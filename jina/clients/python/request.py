__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import mimetypes
import os
import urllib.parse
import uuid
import json
from typing import Iterator, Union, Tuple, Dict

import numpy as np
from google.protobuf import json_format

from ...drivers.helper import guess_mime
from ...enums import ClientMode
from ...helper import batch_iterator, is_url
from ...importer import ImportExtensions
from ...logging import default_logger
from ...proto import jina_pb2, uid
from jina.types.ndarray.generic import NdArray


def _fill_document(document: 'jina_pb2.DocumentProto',
                   content: Union['jina_pb2.DocumentProto', 'np.ndarray', bytes, str, Tuple[
                       Union['jina_pb2.DocumentProto', bytes], Union['jina_pb2.DocumentProto', bytes]]],
                   docs_in_same_batch: int,
                   mime_type: str,
                   buffer_sniff: bool,
                   override_doc_id: bool = True
                   ):
    if isinstance(content, jina_pb2.DocumentProto):
        document.CopyFrom(content)
    elif isinstance(content, np.ndarray):
        NdArray(document.blob).value = content
    elif isinstance(content, bytes):
        document.buffer = content
        if not mime_type and buffer_sniff:
            try:
                import magic

                mime_type = magic.from_buffer(content, mime=True)
            except Exception as ex:
                default_logger.warning(
                    f'can not sniff the MIME type due to the exception {repr(ex)}'
                )
    elif isinstance(content, Dict):
        json_format.ParseDict(content, document)
    elif isinstance(content, str):
        try:
            json_format.Parse(content, document)
        except Exception:
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


def _generate(data: Union[Iterator[Union['jina_pb2.DocumentProto', bytes]], Iterator[
    Tuple[Union['jina_pb2.DocumentProto', bytes], Union['jina_pb2.DocumentProto', bytes]]], Iterator['np.ndarray'], Iterator[
                              str], 'np.ndarray', Iterator[Dict]],
              batch_size: int = 0, mode: ClientMode = ClientMode.INDEX,
              mime_type: str = None,
              override_doc_id: bool = True,
              queryset: Iterator['jina_pb2.QueryLangProto'] = None,
              *args,
              **kwargs,
              ) -> Iterator['jina_pb2.RequestProto']:
    buffer_sniff = False

    with ImportExtensions(required=False,
                          pkg_name='python-magic',
                          help_text=f'can not sniff the MIME type '
                                    f'MIME sniffing requires brew install '
                                    f'libmagic (Mac)/ apt-get install libmagic1 (Linux)'):
        import magic
        buffer_sniff = True

    if mime_type and (mime_type not in mimetypes.types_map.values()):
        mime_type = mimetypes.guess_type(f'*.{mime_type}')[0]

    if isinstance(mode, str):
        mode = ClientMode.from_string(mode)

    _fill = lambda x, y: _fill_document(document=x,
                                        content=y,
                                        docs_in_same_batch=batch_size,
                                        mime_type=mime_type,
                                        buffer_sniff=buffer_sniff,
                                        override_doc_id=override_doc_id
                                        )

    for batch in batch_iterator(data, batch_size):
        req = jina_pb2.RequestProto()
        req.request_id = uuid.uuid1().hex
        if queryset:
            if isinstance(queryset, jina_pb2.QueryLangProto):
                queryset = [queryset]
            req.queryset.extend(queryset)

        _req = getattr(req, str(mode).lower())
        for content in batch:
            d = _req.docs.add()
            if isinstance(content, tuple) and len(content) == 2:
                default_logger.debug('content comes in pair, '
                                     'will take the first as the input and the second as the groundtruth')
                gt = _req.groundtruths.add()
                _fill(d, content[0])
                _fill(gt, content[1])
            else:
                _fill(d, content)
        yield req


def index(*args, **kwargs):
    """Generate a indexing request"""
    yield from _generate(*args, **kwargs)


def train(*args, **kwargs):
    """Generate a training request """
    yield from _generate(*args, **kwargs)
    req = jina_pb2.RequestProto()
    req.request_id = uuid.uuid1().hex
    req.train.flush = True
    yield req


def search(*args, **kwargs):
    """Generate a searching request """
    if ('top_k' in kwargs) and (kwargs['top_k'] is not None):
        top_k_queryset = jina_pb2.QueryLangProto()
        top_k_queryset.name = 'VectorSearchDriver'
        top_k_queryset.priority = 1
        top_k_queryset.parameters['top_k'] = kwargs['top_k']
        if 'queryset' not in kwargs:
            kwargs['queryset'] = [top_k_queryset]
        else:
            kwargs['queryset'].append(top_k_queryset)
    yield from _generate(*args, **kwargs)


def evaluate(*args, **kwargs):
    """Generate an evaluation request """
    yield from _generate(*args, **kwargs)
