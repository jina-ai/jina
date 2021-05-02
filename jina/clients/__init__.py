"""Module wrapping the Client of Jina."""
from functools import partialmethod
from typing import Optional, Dict

from . import request
from .base import BaseClient, CallbackFnType, InputType, InputDeleteType
from .helper import callback_exec
from .request import GeneratorSourceType
from .websocket import WebSocketClientMixin
from .. import Response
from ..enums import RequestType
from ..helper import run_async


class Client(BaseClient):
    """A simple Python client for connecting to the gRPC gateway.

    It manages the asyncio event loop internally, so all interfaces are synchronous from the outside.
    """

    async def _get_results(self, *args, **kwargs):
        result = []
        async for resp in super()._get_results(*args, **kwargs):
            if self.args.return_results:
                result.append(resp)

        if self.args.return_results:
            return result

    def post(
            self,
            on: str,
            inputs: InputType,
            on_done: CallbackFnType = None,
            on_error: CallbackFnType = None,
            on_always: CallbackFnType = None,
            parameters: Optional[Dict] = None,
            target_peapod: Optional[str] = None,
            **kwargs,
    ) -> Optional[Response]:
        """Post a general data request to the Flow.

        :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document id.
        :param on: the endpoint is used for identifying the user-defined ``request_type``, labeled by ``@requests(on='/abc')``
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param parameters: the kwargs that will be sent to the executor
        :param target_peapod: a regex string represent the certain peas/pods request targeted
        :param kwargs: additional parameters
        :return: None
        """
        self.mode = RequestType.DATA
        return run_async(
            self._get_results,
            inputs=inputs,
            on_done=on_done,
            on_error=on_error,
            on_always=on_always,
            exec_endpoint=on,
            target=target_peapod,
            parameters=parameters,
            **kwargs,
        )

    index = partialmethod(post, '/index')
    search = partialmethod(post, '/search')
    update = partialmethod(post, '/update')
    delete = partialmethod(post, '/delete')


class WebSocketClient(Client, WebSocketClientMixin):
    """A Python Client to stream requests from a Flow with a REST Gateway.

    :class:`WebSocketClient` shares the same interface as :class:`Client` and provides methods like
    :meth:`index`, "meth:`search`, :meth:`train`, :meth:`update` & :meth:`delete`.

    It is used by default while running operations when we create a `Flow` with `rest_api=True`

    .. highlight:: python
    .. code-block:: python

        from jina.flow import Flow
        f = Flow(rest_api=True).add().add()

        with f:
            f.index(['abc'])


    :class:`WebSocketClient` can also be used to run operations for a remote Flow

    .. highlight:: python
    .. code-block:: python

        # A Flow running on remote
        from jina.flow import Flow
        f = Flow(rest_api=True, port_expose=34567).add().add()

        with f:
            f.block()

        # Local WebSocketClient running index & search
        from jina.clients import WebSocketClient

        client = WebSocketClient(...)
        client.index(...)
        client.search(...)


    :class:`WebSocketClient` internally handles an event loop to run operations asynchronously.
    """
