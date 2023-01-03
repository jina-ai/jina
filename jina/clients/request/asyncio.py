"""Module for async requests generator."""

from typing import TYPE_CHECKING, AsyncIterator, Dict, Optional

from jina.clients.request.helper import _new_data_request, _new_data_request_from_batch
from jina.enums import DataInputType
from jina.importer import ImportExtensions
from jina.logging.predefined import default_logger

if TYPE_CHECKING:  # pragma: no cover
    from jina.clients.request import GeneratorSourceType
    from jina.types.request import Request


async def request_generator(
    exec_endpoint: str,
    data: Optional['GeneratorSourceType'] = None,
    request_size: int = 0,
    data_type: DataInputType = DataInputType.AUTO,
    target_executor: Optional[str] = None,
    parameters: Optional[Dict] = None,
    **kwargs,  # do not remove this, add on purpose to suppress unknown kwargs
) -> AsyncIterator['Request']:
    """An async :function:`request_generator`.

    :param exec_endpoint: the endpoint string, by convention starts with `/`
    :param data: the data to use in the request
    :param request_size: the number of Documents per request
    :param data_type: if ``data`` is an iterator over self-contained document, i.e. :class:`DocumentSourceType`;
            or an iterator over possible Document content (set to text, blob and buffer).
    :param parameters: the kwargs that will be sent to the executor
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
            with ImportExtensions(required=True):
                import aiostream

            async for batch in aiostream.stream.chunks(data, request_size):
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
