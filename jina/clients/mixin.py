from contextlib import nullcontext
from functools import partialmethod
from typing import Optional, Dict, List, AsyncGenerator

from .base import CallbackFnType, InputType
from ..enums import InfrastructureType
from ..helper import run_async
from ..peapods.pods.k8slib import kubernetes_tools
from ..types.request import Response


class PostMixin:
    """The Post Mixin class for Client and Flow"""

    def post(
        self,
        on: str,
        inputs: Optional[InputType] = None,
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        parameters: Optional[Dict] = None,
        target_peapod: Optional[str] = None,
        request_size: int = 100,
        show_progress: bool = False,
        continue_on_error: bool = False,
        return_results: bool = False,
        **kwargs,
    ) -> Optional[List[Response]]:
        """Post a general data request to the Flow.

        :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document id.
        :param on: the endpoint is used for identifying the user-defined ``request_type``, labeled by ``@requests(on='/abc')``
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param parameters: the kwargs that will be sent to the executor
        :param target_peapod: a regex string. Only matching Executors will process the request.
        :param request_size: the number of Documents per request. <=0 means all inputs in one request.
        :param show_progress: if set, client will show a progress bar on receiving every request.
        :param continue_on_error: if set, a Request that causes callback error will be logged only without blocking the further requests.
        :param return_results: if set, the results of all Requests will be returned as a list. This is useful when one wants process Responses in bulk instead of using callback.
        :param kwargs: additional parameters
        :return: None or list of Response

        .. warning::
            ``target_peapod`` uses ``re.match`` for checking if the pattern is matched.
             ``target_peapod=='foo'`` will match both pods with the name ``foo`` and ``foo_what_ever_suffix``.
        """

        async def _get_results(*args, **kwargs):
            result = []
            c = self.client
            c.show_progress = show_progress
            c.continue_on_error = continue_on_error
            async for resp in c._get_results(*args, **kwargs):
                if return_results:
                    result.append(resp)

            if return_results:
                return result

        if (
            'disable_portforward' not in kwargs.keys()
            and hasattr(self.args, 'infrastructure')
            and self.args.infrastructure == InfrastructureType.K8S
        ):
            context_mgr = kubernetes_tools.get_port_forward_contextmanager(
                self.args.name, self.port_expose
            )
        else:
            context_mgr = nullcontext()
        with context_mgr:
            return run_async(
                _get_results,
                inputs=inputs,
                on_done=on_done,
                on_error=on_error,
                on_always=on_always,
                exec_endpoint=on,
                target_peapod=target_peapod,
                parameters=parameters,
                request_size=request_size,
                **kwargs,
            )

    # ONLY CRUD, for other request please use `.post`
    index = partialmethod(post, '/index')
    search = partialmethod(post, '/search')
    update = partialmethod(post, '/update')
    delete = partialmethod(post, '/delete')


class AsyncPostMixin:
    """The Async Post Mixin class for AsyncClient and AsyncFlow"""

    async def post(
        self,
        on: str,
        inputs: Optional[InputType] = None,
        on_done: CallbackFnType = None,
        on_error: CallbackFnType = None,
        on_always: CallbackFnType = None,
        parameters: Optional[Dict] = None,
        target_peapod: Optional[str] = None,
        request_size: int = 100,
        show_progress: bool = False,
        continue_on_error: bool = False,
        **kwargs,
    ) -> AsyncGenerator[None, Response]:
        """Post a general data request to the Flow.

        :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document id.
        :param on: the endpoint is used for identifying the user-defined ``request_type``, labeled by ``@requests(on='/abc')``
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param parameters: the kwargs that will be sent to the executor
        :param target_peapod: a regex string. Only matching Executors will process the request.
        :param request_size: the number of Documents per request. <=0 means all inputs in one request.
        :param show_progress: if set, client will show a progress bar on receiving every request.
        :param continue_on_error: if set, a Request that causes callback error will be logged only without blocking the further requests.
        :param kwargs: additional parameters
        :yield: Response object
        """
        c = self.client
        c.show_progress = show_progress
        c.continue_on_error = continue_on_error
        async for r in c._get_results(
            inputs=inputs,
            on_done=on_done,
            on_error=on_error,
            on_always=on_always,
            exec_endpoint=on,
            target_peapod=target_peapod,
            parameters=parameters,
            request_size=request_size,
            **kwargs,
        ):
            yield r

    # ONLY CRUD, for other request please use `.post`
    index = partialmethod(post, '/index')
    search = partialmethod(post, '/search')
    update = partialmethod(post, '/update')
    delete = partialmethod(post, '/delete')
