import asyncio
from contextlib import AsyncExitStack, nullcontext
from typing import TYPE_CHECKING, Optional

from jina.clients.base import BaseClient
from jina.clients.base.helper import HTTPClientlet
from jina.clients.helper import callback_exec, callback_exec_on_error
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
        :param kwargs: kwargs for _get_task_name and _get_requests
        :yields: generator over results
        """
        with ImportExtensions(required=True):
            import aiohttp

        self.inputs = inputs
        request_iterator = self._get_requests(**kwargs)

        async with AsyncExitStack() as stack:
            try:
                cm1 = ProgressBar(
                    total_length=self._inputs_length, disable=not (self.show_progress)
                )
                p_bar = stack.enter_context(cm1)

                proto = 'https' if self.args.tls else 'http'
                url = f'{proto}://{self.args.host}:{self.args.port}/post'
                iolet = await stack.enter_async_context(
                    HTTPClientlet(url=url, logger=self.logger)
                )

                def _request_handler(request: 'Request') -> 'asyncio.Future':
                    """
                    For HTTP Client, for each request in the iterator, we `send_message` using
                    http POST request and add it to the list of tasks which is awaited and yielded.
                    :param request: current request in the iterator
                    :return: asyncio Task for sending message
                    """
                    return asyncio.ensure_future(iolet.send_message(request=request))

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
                    if r_status == 404:
                        raise BadClient(f'no such endpoint {url}')
                    elif r_status < 200 or r_status > 300:
                        raise ValueError(r_str)

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

            except aiohttp.ClientError as e:
                self.logger.error(
                    f'Error while fetching response from HTTP server {e!r}'
                )

                if on_error or on_always:
                    if on_error:
                        callback_exec_on_error(on_error, e, self.logger)
                    if on_always:
                        callback_exec(
                            response=None,
                            on_error=None,
                            on_done=None,
                            on_always=on_always,
                            continue_on_error=self.continue_on_error,
                            logger=self.logger,
                        )
                else:
                    raise e
