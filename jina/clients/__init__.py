"""Module wrapping the Client of Jina."""
__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Union, List

from . import request
from .base import BaseClient, CallbackFnType, InputType, InputDeleteType
from .helper import callback_exec
from .request import GeneratorSourceType
from .websocket import WebSocketClientMixin
from ..enums import RequestType
from ..helper import run_async, deprecated_alias


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

    @deprecated_alias(
        input_fn=('inputs', 0),
        buffer=('inputs', 1),
        callback=('on_done', 1),
        output_fn=('on_done', 1),
    )
    def train(
        self,
        inputs: InputType,
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        **kwargs,
    ) -> None:
        """Issue 'train' request to the Flow.

        :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: additional parameters
        :return: None
        """
        self.mode = RequestType.TRAIN
        return run_async(
            self._get_results, inputs, on_done, on_error, on_always, **kwargs
        )

    @deprecated_alias(
        input_fn=('inputs', 0),
        buffer=('inputs', 1),
        callback=('on_done', 1),
        output_fn=('on_done', 1),
    )
    def search(
        self,
        inputs: InputType,
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        **kwargs,
    ) -> None:
        """Issue 'search' request to the Flow.

        :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: additional parameters
        :return: None
        """
        self.mode = RequestType.SEARCH
        self.add_default_kwargs(kwargs)
        return run_async(
            self._get_results, inputs, on_done, on_error, on_always, **kwargs
        )

    @deprecated_alias(
        input_fn=('inputs', 0),
        buffer=('inputs', 1),
        callback=('on_done', 1),
        output_fn=('on_done', 1),
    )
    def index(
        self,
        inputs: InputType,
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        **kwargs,
    ) -> None:
        """Issue 'index' request to the Flow.

        :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: additional parameters
        :return: None
        """
        self.mode = RequestType.INDEX
        return run_async(
            self._get_results, inputs, on_done, on_error, on_always, **kwargs
        )

    @deprecated_alias(
        input_fn=('inputs', 0),
        buffer=('inputs', 1),
        callback=('on_done', 1),
        output_fn=('on_done', 1),
    )
    def update(
        self,
        inputs: InputType,
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        **kwargs,
    ) -> None:
        """Issue 'update' request to the Flow.

        :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: additional parameters
        :return: None
        """
        self.mode = RequestType.UPDATE
        return run_async(
            self._get_results, inputs, on_done, on_error, on_always, **kwargs
        )

    @deprecated_alias(
        input_fn=('inputs', 0),
        buffer=('inputs', 1),
        callback=('on_done', 1),
        output_fn=('on_done', 1),
    )
    def delete(
        self,
        inputs: InputDeleteType,
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        **kwargs,
    ) -> None:
        """Issue 'update' request to the Flow.

        :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document id.
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: additional parameters
        :return: None
        """
        self.mode = RequestType.DELETE
        return run_async(
            self._get_results, inputs, on_done, on_error, on_always, **kwargs
        )

    def reload(
        self,
        targets: Union[str, List[str]],
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        **kwargs,
    ):
        """Send 'reload' request to the Flow.

        :param targets: the regex string or list of regex strings to match the pea/pod names.
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param kwargs: additional parameters
        :return: None
        """

        if isinstance(targets, str):
            targets = [targets]
        kwargs['targets'] = targets

        self.mode = RequestType.CONTROL
        return run_async(
            self._get_results,
            [],
            on_done,
            on_error,
            on_always,
            command='RELOAD',
            **kwargs,
        )


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
