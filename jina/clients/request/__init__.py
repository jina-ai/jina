"""Module for Jina Requests."""
__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterator, Union, Tuple, AsyncIterable, Iterable, Optional, Sequence

from .helper import _new_data_request_from_batch
from ... import Request
from ...enums import RequestType, DataInputType
from ...helper import batch_iterator
from ...logging import default_logger
from ...types.document import DocumentSourceType, DocumentContentType, Document
from ...types.sets.querylang import AcceptQueryLangType

SingletonDataType = Union[
    DocumentContentType,
    DocumentSourceType,
    Document,
    Tuple[DocumentContentType, DocumentContentType],
    Tuple[DocumentSourceType, DocumentSourceType],
]

GeneratorSourceType = Union[
    Document, Iterable[SingletonDataType], AsyncIterable[SingletonDataType]
]


def request_generator(
    data: GeneratorSourceType,
    exec_endpoint: Optional[str] = None,
    request_size: int = 0,
    mime_type: Optional[str] = None,
    queryset: Optional[
        Union[AcceptQueryLangType, Iterator[AcceptQueryLangType]]
    ] = None,
    data_type: DataInputType = DataInputType.AUTO,
    target_peapod: Optional[str] = None,
    parameters: Optional[dict] = None,
    **kwargs,  # do not remove this, add on purpose to suppress unknown kwargs
) -> Iterator['Request']:
    """Generate a request iterator.

    :param data: the data to use in the request
    :param request_size: the request size for the client
    :param mode: the request mode (index, search etc.)
    :param mime_type: mime type
    :param queryset: querylang set of queries
    :param data_type: if ``data`` is an iterator over self-contained document, i.e. :class:`DocumentSourceType`;
            or an iterator over possible Document content (set to text, blob and buffer).
    :param kwargs: additional arguments
    :yield: request
    """

    _kwargs = dict(mime_type=mime_type, weight=1.0, extra_kwargs=kwargs)

    try:
        if not isinstance(data, Iterable):
            data = [data]
        for batch in batch_iterator(data, request_size):
            yield _new_data_request_from_batch(
                _kwargs=kwargs,
                batch=batch,
                data_type=data_type,
                queryset=queryset,
                endpoint=exec_endpoint,
                target=target_peapod,
                parameters=parameters,
            )

    except Exception as ex:
        # must be handled here, as grpc channel wont handle Python exception
        default_logger.critical(f'inputs is not valid! {ex!r}', exc_info=True)
