from abc import ABC
from contextlib import nullcontext
from typing import Callable, Optional

from .base import BaseClient, InputType
from .grpc import GRPCClient
from .helper import callback_exec
from ..importer import ImportExtensions
from ..logging.profile import TimeContext, ProgressBar
from ..types.request import Request


class HTTPClientMixin(BaseClient, ABC):
    """A MixIn for HTTP Client."""

    async def _get_results(
        self,
        inputs: InputType,
        on_done: Callable,
        on_error: Optional[Callable] = None,
        on_always: Optional[Callable] = None,
        **kwargs,
    ):
        """
        :meth:`send_requests()`
            Traverses through the request iterator
            Sends each request & awaits :meth:`websocket.send()`
            Sends & awaits `byte(True)` to acknowledge request iterator is empty
        Traversal logic:
            Starts an independent task :meth:`send_requests()`
            Awaits on each response from :meth:`websocket.recv()` (done in an async loop)
            This makes sure client makes concurrent invocations
        Await exit strategy:
            :meth:`send_requests()` keeps track of num_requests sent
            Async recv loop keeps track of num_responses received
            Client exits out of await when num_requests == num_responses

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

        req_iter = self._get_requests(**kwargs)
        async with aiohttp.ClientSession() as session:
            if self.args.show_progress:
                cm1, cm2 = ProgressBar(), TimeContext('')
            else:
                cm1, cm2 = nullcontext(), nullcontext()
            try:
                with cm1 as p_bar, cm2:
                    for req in req_iter:
                        # fix the mismatch between pydantic model and Protobuf model
                        req_dict = req.dict()
                        req_dict['data'] = req_dict['data'].get('docs', None)

                        async with session.post(
                            f'http://{self.args.host}:{self.args.port_expose}/post',
                            json=req_dict,
                        ) as response:
                            resp_str = await response.json()
                            if response.status == 404:
                                raise ConnectionError('no such endpoint on server')
                            resp = Request(resp_str)
                            resp = resp.as_typed_request(
                                resp.request_type
                            ).as_response()
                            callback_exec(
                                response=resp,
                                on_error=on_error,
                                on_done=on_done,
                                on_always=on_always,
                                continue_on_error=self.args.continue_on_error,
                                logger=self.logger,
                            )
                            if self.args.show_progress:
                                p_bar.update(self.args.request_size)
                            yield resp
            except aiohttp.client_exceptions.ClientConnectorError:
                self.logger.warning(f'Client got disconnected from the HTTP server')


class HTTPClient(GRPCClient, HTTPClientMixin):
    """A Python Client to stream requests from a Flow with a REST Gateway.

    :class:`WebSocketClient` shares the same interface as :class:`Client` and provides methods like
    :meth:`index`, "meth:`search`, :meth:`train`, :meth:`update` & :meth:`delete`.

    It is used by default while running operations when we create a `Flow` with `restful=True`

    .. highlight:: python
    .. code-block:: python

        from jina.flow import Flow
        f = Flow(protocol='http').add().add()

        with f:
            f.index(['abc'])


    :class:`WebSocketClient` can also be used to run operations for a remote Flow

    .. highlight:: python
    .. code-block:: python

        # A Flow running on remote
        from jina.flow import Flow
        f = Flow(protocol='http', port_expose=34567).add().add()

        with f:
            f.block()

        # Local WebSocketClient running index & search
        from jina.clients import WebSocketClient

        client = WebSocketClient(...)
        client.index(...)
        client.search(...)


    :class:`WebSocketClient` internally handles an event loop to run operations asynchronously.
    """
