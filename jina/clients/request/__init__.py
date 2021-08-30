"""Module for Jina Requests."""

from typing import Iterator, Union, Tuple, AsyncIterable, Iterable, Optional, Dict

from .helper import _new_data_request_from_batch, _new_data_request
from ...enums import DataInputType
from ...helper import batch_iterator
from ...logging.predefined import default_logger
from ...types.document import DocumentSourceType, DocumentContentType, Document
from ...types.request import Request

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
    data: GeneratorSourceType,
    request_size: int = 0,
    data_type: DataInputType = DataInputType.AUTO,
    target_peapod: Optional[str] = None,
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
    :param target_peapod: a regex string. Only matching Executors will process the request.
    :param kwargs: additional arguments
    :yield: request
    """

    _kwargs = dict(extra_kwargs=kwargs)

    try:
        if data is None:
            # this allows empty inputs, i.e. a data request with only parameters
            yield _new_data_request(
                endpoint=exec_endpoint, target=target_peapod, parameters=parameters
            )
        else:
            if not isinstance(data, Iterable):
                data = [data]
            for batch in batch_iterator(data, request_size):
                yield _new_data_request_from_batch(
                    _kwargs=kwargs,
                    batch=batch,
                    data_type=data_type,
                    endpoint=exec_endpoint,
                    target=target_peapod,
                    parameters=parameters,
                )

    except Exception as ex:
        # must be handled here, as grpc channel wont handle Python exception
        default_logger.critical(f'inputs is not valid! {ex!r}', exc_info=True)
