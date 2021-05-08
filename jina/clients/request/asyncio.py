"""Module for async requests generator."""

from typing import AsyncIterator, Optional

from .helper import _new_data_request_from_batch
from .. import GeneratorSourceType
from ... import Request
from ...enums import RequestType, DataInputType
from ...importer import ImportExtensions
from ...logging import default_logger


async def request_generator(
    data: GeneratorSourceType,
    exec_endpoint: str,
    request_size: int = 0,
    mode: RequestType = RequestType.INDEX,
    mime_type: Optional[str] = None,
    data_type: DataInputType = DataInputType.AUTO,
    peapod_target: Optional[str] = None,
    **kwargs,  # do not remove this, add on purpose to suppress unknown kwargs
) -> AsyncIterator['Request']:
    """An async :function:`request_generator`.

    :param data: the data to use in the request
    :param request_size: the request size for the client
    :param mode: the request mode (index, search etc.)
    :param mime_type: mime type
    :param data_type: if ``data`` is an iterator over self-contained document, i.e. :class:`DocumentSourceType`;
            or an iterator over possible Document content (set to text, blob and buffer).
    :param kwargs: additional key word arguments
    :yield: request
    """
    _kwargs = dict(mime_type=mime_type, weight=1.0)

    try:
        with ImportExtensions(required=True):
            import aiostream

        async for batch in aiostream.stream.chunks(data, request_size):
            yield _new_data_request_from_batch(
                _kwargs, batch, data_type, mode, queryset, exec_endpoint, peapod_target
            )
    except Exception as ex:
        # must be handled here, as grpc channel wont handle Python exception
        default_logger.critical(f'inputs is not valid! {ex!r}', exc_info=True)
