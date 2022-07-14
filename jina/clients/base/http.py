import asyncio
from contextlib import AsyncExitStack
from typing import TYPE_CHECKING, Optional, Tuple

from starlette import status

from jina.clients.base import BaseClient
from jina.clients.base.helper import HTTPClientlet
from jina.clients.helper import callback_exec
from jina.excepts import BadClient
from jina.importer import ImportExtensions
from jina.logging.profile import ProgressBar
from jina.serve.stream import RequestStreamer
from jina.types.request import Request
from jina.types.request.data import DataRequest

if TYPE_CHECKING:
    from jina.clients.base import CallbackFnType, InputType


class HTTPBaseClient(BaseClient):
    """A MixIn for HTTP Client."""

    def _handle_response_status(self, r_status, r_str, url):
        if r_status == status.HTTP_404_NOT_FOUND:
            raise BadClient(f'no such endpoint {url}')
        elif (
            r_status == status.HTTP_503_SERVICE_UNAVAILABLE
            or r_status == status.HTTP_504_GATEWAY_TIMEOUT
        ):
            if (
                'header' in r_str
                and 'status' in r_str['header']
                and 'description' in r_str['header']['status']
            ):
                raise ConnectionError(r_str['header']['status']['description'])
            else:
                raise ValueError(r_str)
        elif (
            r_status < status.HTTP_200_OK or r_status > status.HTTP_300_MULTIPLE_CHOICES
        ):  # failure codes
            raise ValueError(r_str)

    async def _dry_run(self, **kwargs) -> bool:
        """Sends a dry run to the Flow to validate if the Flow is ready to receive requests

        :param kwargs: kwargs coming from the public interface. Includes arguments to be passed to the `HTTPClientlet`
        :return: boolean indicating the health/readiness of the Flow
        """
        from jina.proto import jina_pb2

        async with AsyncExitStack() as stack:
            try:
                proto = 'https' if self.args.tls else 'http'
                url = f'{proto}://{self.args.host}:{self.args.port}/dry_run'
                iolet = await stack.enter_async_context(
                    HTTPClientlet(url=url, logger=self.logger, **kwargs)
                )

                response = await iolet.send_dry_run(**kwargs)
                r_status = response.status

                r_str = await response.json()
                self._handle_response_status(r_status, r_str, url)
                if r_str['code'] == jina_pb2.StatusProto.SUCCESS:
                    return True
                else:
                    self.logger.debug(
                        f'Returned code is not expected! Description: {r_str["description"]}'
                    )
            except Exception as e:
                self.logger.error(
                    f'Error while fetching response from HTTP server {e!r}'
                )
        return False

    async def _get_results(
        self,
        inputs: 'InputType',
        on_done: 'CallbackFnType',
        on_error: Optional['CallbackFnType'] = None,
        on_always: Optional['CallbackFnType'] = None,
        **kwargs,
    ):
        """
        :param inputs: the callable
        :param on_done: the callback for on_done
        :param on_error: the callback for on_error
        :param on_always: the callback for on_always
        :param kwargs: kwargs coming from the public interface. Includes arguments to be passed to the `HTTPClientlet`
        :yields: generator over results
        """
        with ImportExtensions(required=True):
            import aiohttp

        self.inputs = inputs
        request_iterator = self._get_requests(**kwargs)

        async with AsyncExitStack() as stack:
            cm1 = ProgressBar(
                total_length=self._inputs_length, disable=not (self.show_progress)
            )
            p_bar = stack.enter_context(cm1)

            proto = 'https' if self.args.tls else 'http'
            url = f'{proto}://{self.args.host}:{self.args.port}/post'
            iolet = await stack.enter_async_context(
                HTTPClientlet(url=url, logger=self.logger, **kwargs)
            )

            def _request_handler(
                request: 'Request',
            ) -> 'Tuple[asyncio.Future, Optional[asyncio.Future]]':
                """
                For HTTP Client, for each request in the iterator, we `send_message` using
                http POST request and add it to the list of tasks which is awaited and yielded.
                :param request: current request in the iterator
                :return: asyncio Task for sending message
                """
                return asyncio.ensure_future(iolet.send_message(request=request)), None

            def _result_handler(result):
                return result

            streamer = RequestStreamer(
                self.args,
                request_handler=_request_handler,
                result_handler=_result_handler,
            )
            async for response in streamer.stream(request_iterator):
                r_status = response.status

                r_str = await response.json()
                self._handle_response_status(r_status, r_str, url)

                da = None
                if 'data' in r_str and r_str['data'] is not None:
                    from docarray import DocumentArray

                    da = DocumentArray.from_dict(r_str['data'])
                    del r_str['data']

                resp = DataRequest(r_str)
                if da is not None:
                    resp.data.docs = da

                callback_exec(
                    response=resp,
                    on_error=on_error,
                    on_done=on_done,
                    on_always=on_always,
                    continue_on_error=self.continue_on_error,
                    logger=self.logger,
                )
                if self.show_progress:
                    p_bar.update()
                yield resp
