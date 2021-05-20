from functools import partialmethod
from typing import Optional, Dict, List, AsyncGenerator

from .base import CallbackFnType, InputType
from ..helper import run_async
from ..types.request import Response


class PostMixin:
    """The Post Mixin class for Client and Flow """

    def post(
        self,
        on: str,
        inputs: Optional[InputType] = None,
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        parameters: Optional[Dict] = None,
        target_peapod: Optional[str] = None,
        **kwargs,
    ) -> Optional[List[Response]]:
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

        async def _get_results(*args, **kwargs):
            result = []
            c = self.client
            async for resp in c._get_results(*args, **kwargs):
                if c.args.return_results:
                    result.append(resp)

            if c.args.return_results:
                return result

        return run_async(
            _get_results,
            inputs=inputs,
            on_done=on_done,
            on_error=on_error,
            on_always=on_always,
            exec_endpoint=on,
            target_peapod=target_peapod,
            parameters=parameters,
            **kwargs,
        )

    # ONLY CRUD, for other request please use `.post`
    index = partialmethod(post, '/index')
    search = partialmethod(post, '/search')
    update = partialmethod(post, '/update')
    delete = partialmethod(post, '/delete')


class AsyncPostMixin:
    """The Async Post Mixin class for AsyncClient and AsyncFlow """

    async def post(
        self,
        on: str,
        inputs: Optional[InputType] = None,
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        parameters: Optional[Dict] = None,
        target_peapod: Optional[str] = None,
        **kwargs,
    ) -> AsyncGenerator[None, Response]:
        """Post a general data request to the Flow.

        :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document id.
        :param on: the endpoint is used for identifying the user-defined ``request_type``, labeled by ``@requests(on='/abc')``
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param parameters: the kwargs that will be sent to the executor
        :param target_peapod: a regex string represent the certain peas/pods request targeted
        :param kwargs: additional parameters
        :yield: Response object
        """
        async for r in self.client._get_results(
            inputs=inputs,
            on_done=on_done,
            on_error=on_error,
            on_always=on_always,
            exec_endpoint=on,
            target_peapod=target_peapod,
            parameters=parameters,
            **kwargs,
        ):
            yield r

    # ONLY CRUD, for other request please use `.post`
    index = partialmethod(post, '/index')
    search = partialmethod(post, '/search')
    update = partialmethod(post, '/update')
    delete = partialmethod(post, '/delete')
