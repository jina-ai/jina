__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterator, Union, Tuple, Sequence

from .. import Request
from ..enums import RequestType, DataInputType
from ..excepts import BadDocType
from ..helper import batch_iterator
from ..logging import default_logger
from ..types.document import Document, DocumentSourceType, DocumentContentType
from ..types.querylang import QueryLang
from ..types.sets.querylang import AcceptQueryLangType

GeneratorSourceType = Iterator[Union[DocumentContentType,
                                     DocumentSourceType,
                                     Tuple[DocumentContentType, DocumentContentType],
                                     Tuple[DocumentSourceType, DocumentSourceType]]]


def _build_doc(data, data_type: DataInputType, **kwargs) -> Tuple['Document', 'DataInputType']:
    def _build_doc_from_content():
        with Document(**kwargs) as d:
            d.content = data
        return d, DataInputType.CONTENT

    if data_type == DataInputType.AUTO or data_type == DataInputType.DOCUMENT:
        if isinstance(data, Document):
            # if incoming is already primitive type Document, then all good, best practice!
            return data, DataInputType.DOCUMENT
        try:
            d = Document(data, **kwargs)
            return d, DataInputType.DOCUMENT
        except BadDocType:
            # AUTO has a fallback, now reconsider it as content
            if data_type == DataInputType.AUTO:
                return _build_doc_from_content()
            else:
                raise
    elif data_type == DataInputType.CONTENT:
        return _build_doc_from_content()


def _generate(data: GeneratorSourceType,
              request_size: int = 0,
              mode: RequestType = RequestType.INDEX,
              mime_type: str = None,
              queryset: Union[AcceptQueryLangType, Iterator[AcceptQueryLangType]] = None,
              data_type: DataInputType = DataInputType.AUTO,
              **kwargs  # do not remove this, add on purpose to suppress unknown kwargs
              ) -> Iterator['Request']:
    """
    :param data_type: if ``data`` is an iterator over self-contained document, i.e. :class:`DocumentSourceType`;
            or an interator over possible Document content (set to text, blob and buffer).
    :return:
    """

    _kwargs = dict(mime_type=mime_type, length=request_size, weight=1.0)

    try:
        for batch in batch_iterator(data, request_size):
            req = Request()
            req.request_type = str(mode)
            for content in batch:
                if isinstance(content, tuple) and len(content) == 2:
                    # content comes in pair,  will take the first as the input and the second as the groundtruth

                    # note how data_type is cached
                    d, data_type = _build_doc(content[0], data_type, **_kwargs)
                    gt, _ = _build_doc(content[1], data_type, **_kwargs)
                    req.docs.append(d)
                    req.groundtruths.append(gt)
                else:
                    d, data_type = _build_doc(content, data_type, **_kwargs)
                    req.docs.append(d)

            if isinstance(queryset, Sequence):
                req.queryset.extend(queryset)
            elif queryset is not None:
                req.queryset.append(queryset)

            yield req
    except Exception as ex:
        # must be handled here, as grpc channel wont handle Python exception
        default_logger.critical(f'input_fn is not valid! {ex!r}', exc_info=True)


def index(*args, **kwargs):
    """Generate a indexing request"""
    yield from _generate(*args, **kwargs)


def update(*args, **kwargs):
    """Generate a update request"""
    yield from _generate(*args, **kwargs)


def delete(*args, **kwargs):
    """Generate a delete request"""
    yield from _generate(*args, **kwargs)


def train(*args, **kwargs):
    """Generate a training request """
    yield from _generate(*args, **kwargs)
    req = Request()
    req.train.flush = True
    yield req


def search(*args, **kwargs):
    """Generate a searching request """
    if ('top_k' in kwargs) and (kwargs['top_k'] is not None):
        # associate all VectorSearchDriver and SliceQL driver to use top_k
        # TODO: not really elegant, to be refactored (Han)
        from ..drivers.querylang.slice import SliceQL
        from ..drivers.search import VectorSearchDriver
        topk_ql = [QueryLang(SliceQL(start=0, end=kwargs['top_k'], priority=1)),
                   QueryLang(VectorSearchDriver(top_k=kwargs['top_k'], priority=1))]
        if 'queryset' not in kwargs:
            kwargs['queryset'] = topk_ql
        else:
            kwargs['queryset'].extend(topk_ql)
    yield from _generate(*args, **kwargs)


def evaluate(*args, **kwargs):
    """Generate an evaluation request """
    yield from _generate(*args, **kwargs)
