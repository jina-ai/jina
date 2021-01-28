__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterator, Union, Tuple, AsyncIterator

from .helper import _new_request_from_batch
from ... import Request
from ...enums import RequestType, DataInputType
from ...helper import batch_iterator
from ...logging import default_logger
from ...types.document import DocumentSourceType, DocumentContentType
from ...types.sets.querylang import AcceptQueryLangType

SingletonDataType = Union[DocumentContentType,
                          DocumentSourceType,
                          Tuple[DocumentContentType, DocumentContentType],
                          Tuple[DocumentSourceType, DocumentSourceType]]

GeneratorSourceType = Union[Iterator[SingletonDataType], AsyncIterator[SingletonDataType]]


def request_generator(data: GeneratorSourceType,
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
            yield _new_request_from_batch(_kwargs, batch, data_type, mode, queryset)

    except Exception as ex:
        # must be handled here, as grpc channel wont handle Python exception
        default_logger.critical(f'input_fn is not valid! {ex!r}', exc_info=True)
