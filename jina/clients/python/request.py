__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterator, Union, Tuple, Dict, TypeVar, Sequence

from ... import Request
from ...enums import ClientMode
from ...helper import batch_iterator
from ...logging import default_logger
from ...proto import jina_pb2
from ...types.document import Document
from ...types.querylang import QueryLang

DocumentSourceType = TypeVar('DocumentSourceType',
                             jina_pb2.DocumentProto, bytes, str, Dict)


def _generate(data: Union[Iterator[DocumentSourceType],
                          Iterator[Tuple[DocumentSourceType, DocumentSourceType]]],
              batch_size: int = 0,
              mode: ClientMode = ClientMode.INDEX,
              mime_type: str = None,
              override_doc_id: bool = True,
              queryset: Sequence['QueryLang'] = None,
              ) -> Iterator['jina_pb2.RequestProto']:
    if isinstance(mode, str):
        mode = ClientMode.from_string(mode)

    for batch in batch_iterator(data, batch_size):
        req = Request()
        for content in batch:
            _kwargs = dict(mime_type=mime_type, length=batch_size, weight=1.0)
            if isinstance(content, tuple) and len(content) == 2:
                default_logger.debug('content comes in pair, '
                                     'will take the first as the input and the second as the groundtruth')
                d = Document(content[0], **_kwargs)
                gt = Document(content[1], **_kwargs)
                if override_doc_id:
                    d.update_id()
                    gt.update_id()
                req.add_document(d, mode)
                req.add_groundtruth(gt, mode)
            else:
                d = Document(content, **_kwargs)
                if override_doc_id:
                    d.update_id()
                req.add_document(d, mode)

        for q in queryset:
            req.add_querylang(q)

        yield req.as_pb_object


def index(*args, **kwargs):
    """Generate a indexing request"""
    yield from _generate(*args, **kwargs)


def train(*args, **kwargs):
    """Generate a training request """
    yield from _generate(*args, **kwargs)
    req = Request()
    req.train.flush = True
    yield req.as_pb_object


def search(*args, **kwargs):
    """Generate a searching request """
    if ('top_k' in kwargs) and (kwargs['top_k'] is not None):
        topk_ql = QueryLang('VectorSearchDriver', top_k=kwargs['top_k'])
        if 'queryset' not in kwargs:
            kwargs['queryset'] = [topk_ql]
        else:
            kwargs['queryset'].append(topk_ql)
    yield from _generate(*args, **kwargs)


def evaluate(*args, **kwargs):
    """Generate an evaluation request """
    yield from _generate(*args, **kwargs)
