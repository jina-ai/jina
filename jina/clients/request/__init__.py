"""Module for Jina Requests."""

from typing import (
    TYPE_CHECKING,
    AsyncIterable,
    Dict,
    Iterable,
    Iterator,
    Optional,
    Tuple,
    Union,
)

from jina._docarray import Document
from jina.clients.request.helper import _new_data_request, _new_data_request_from_batch
from jina.enums import DataInputType
from jina.helper import batch_iterator
from jina.logging.predefined import default_logger

if TYPE_CHECKING:  # pragma: no cover
    from jina._docarray import Document
    from jina._docarray.document import DocumentSourceType
    from jina._docarray.document.mixins.content import DocumentContentType
    from jina.types.request import Request

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
    exec_endpoint: str,
    data: Optional['GeneratorSourceType'] = None,
    request_size: int = 0,
    data_type: DataInputType = DataInputType.AUTO,
    target_executor: Optional[str] = None,
    parameters: Optional[Dict] = None,
    **kwargs,  # do not remove this, add on purpose to suppress unknown kwargs
) -> Iterator['Request']:
    """Generate a request iterator.

    :param exec_endpoint: the endpoint string, by convention starts with `/`
    :param data: data to send, a list of dict/string/bytes that can be converted into a list of `Document` objects
    :param request_size: the number of the `Documents` in each request
    :param data_type: if ``data`` is an iterator over self-contained document, i.e. :class:`DocumentSourceType`;
            or an iterator over possible Document content (set to text, blob and buffer).
    :param parameters: a dictionary of parameters to be sent to the executor
    :param target_executor: a regex string. Only matching Executors will process the request.
    :param kwargs: additional arguments
    :yield: request
    """

    try:
        if data is None:
            # this allows empty inputs, i.e. a data request with only parameters
            yield _new_data_request(
                endpoint=exec_endpoint, target=target_executor, parameters=parameters
            )
        else:
            if not isinstance(data, Iterable) or isinstance(data, Document):
                data = [data]
            for batch in batch_iterator(data, request_size):
                yield _new_data_request_from_batch(
                    batch=batch,
                    data_type=data_type,
                    endpoint=exec_endpoint,
                    target=target_executor,
                    parameters=parameters,
                )

    except Exception as ex:
        # must be handled here, as grpc channel wont handle Python exception
        default_logger.critical(f'inputs is not valid! {ex!r}', exc_info=True)
        raise
