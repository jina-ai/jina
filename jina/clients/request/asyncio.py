__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterator, Union, AsyncIterator

from .helper import _new_request_from_batch
from .. import GeneratorSourceType
from ... import Request
from ...enums import RequestType, DataInputType
from ...importer import ImportExtensions
from ...logging import default_logger
from ...types.sets.querylang import AcceptQueryLangType


async def request_generator(data: GeneratorSourceType,
                            request_size: int = 0,
                            mode: RequestType = RequestType.INDEX,
                            mime_type: str = None,
                            queryset: Union[AcceptQueryLangType, Iterator[AcceptQueryLangType]] = None,
                            data_type: DataInputType = DataInputType.AUTO,
                            **kwargs  # do not remove this, add on purpose to suppress unknown kwargs
                            ) -> AsyncIterator['Request']:

    _kwargs = dict(mime_type=mime_type, length=request_size, weight=1.0)

    try:
        with ImportExtensions(required=True):
            import aiostream

        async for batch in aiostream.stream.chunks(data, request_size):
            yield _new_request_from_batch(_kwargs, batch, data_type, mode, queryset)
    except Exception as ex:
        # must be handled here, as grpc channel wont handle Python exception
        default_logger.critical(f'input_fn is not valid! {ex!r}', exc_info=True)
