__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from . import request
from .base import BaseClient, CallbackFnType, InputFnType
from .helper import callback_exec
from .request import GeneratorSourceType
from .websockets import WebSocketClientMixin
from ..enums import RequestType
from ..helper import run_async, deprecated_alias


class Client(BaseClient):
    """A simple Python client for connecting to the gRPC gateway.
    It manages the asyncio eventloop internally, so all interfaces are synchronous from the outside.
    """

    @deprecated_alias(buffer=('input_fn', 1), callback=('on_done', 1), output_fn=('on_done', 1))
    def train(self, input_fn: InputFnType = None,
              on_done: CallbackFnType = None,
              on_error: CallbackFnType = None,
              on_always: CallbackFnType = None,
              **kwargs) -> None:
        """

        :param input_fn: the input function that generates the content
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs:
        :return:
        """
        self.mode = RequestType.TRAIN
        return run_async(self._get_results, input_fn, on_done, on_error, on_always, **kwargs)

    @deprecated_alias(buffer=('input_fn', 1), callback=('on_done', 1), output_fn=('on_done', 1))
    def search(self, input_fn: InputFnType = None,
               on_done: CallbackFnType = None,
               on_error: CallbackFnType = None,
               on_always: CallbackFnType = None,
               **kwargs) -> None:
        """

        :param input_fn: the input function that generates the content
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs:
        :return:
        """
        self.mode = RequestType.SEARCH
        return run_async(self._get_results, input_fn, on_done, on_error, on_always, **kwargs)

    @deprecated_alias(buffer=('input_fn', 1), callback=('on_done', 1), output_fn=('on_done', 1))
    def index(self, input_fn: InputFnType = None,
              on_done: CallbackFnType = None,
              on_error: CallbackFnType = None,
              on_always: CallbackFnType = None,
              **kwargs) -> None:
        """

        :param input_fn: the input function that generates the content
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs:
        :return:
        """
        self.mode = RequestType.INDEX
        return run_async(self._get_results, input_fn, on_done, on_error, on_always, **kwargs)

    @deprecated_alias(buffer=('input_fn', 1), callback=('on_done', 1), output_fn=('on_done', 1))
    def update(self, input_fn: InputFnType = None,
               on_done: CallbackFnType = None,
               on_error: CallbackFnType = None,
               on_always: CallbackFnType = None,
               **kwargs) -> None:
        """

        :param input_fn: the input function that generates the content
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs:
        :return:
        """
        self.mode = RequestType.UPDATE
        return run_async(self._get_results, input_fn, on_done, on_error, on_always, **kwargs)

    @deprecated_alias(buffer=('input_fn', 1), callback=('on_done', 1), output_fn=('on_done', 1))
    def delete(self, input_fn: InputFnType = None,
               on_done: CallbackFnType = None,
               on_error: CallbackFnType = None,
               on_always: CallbackFnType = None,
               **kwargs) -> None:
        """

        :param input_fn: the input function that generates the content
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs:
        :return:
        """
        self.mode = RequestType.DELETE
        return run_async(self._get_results, input_fn, on_done, on_error, on_always, **kwargs)


class WebSocketClient(Client, WebSocketClientMixin):
    """A Python Client to stream requests from a Flow with a RESTGateway
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
