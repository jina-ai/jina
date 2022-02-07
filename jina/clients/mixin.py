from functools import partialmethod
from typing import Optional, Dict, List, AsyncGenerator, TYPE_CHECKING, Union
import warnings

from jina.helper import run_async

if TYPE_CHECKING:
    from jina.clients.base import CallbackFnType, InputType
    from jina.types.request import Response
    from jina import DocumentArray


def _include_results_field_in_param(parameters: Optional['Dict']) -> 'Dict':
    key_result = '__results__'

    if parameters:

        if key_result in parameters:
            if not isinstance(parameters[key_result], dict):
                warnings.warn(
                    f'It looks like you passed a dictionary with the key `{key_result}` to `parameters`.'
                    'This key is reserved, so the associated value will be deleted.'
                )
                parameters.update({key_result: dict()})
    else:
        parameters = {key_result: dict()}

    return parameters


class PostMixin:
    """The Post Mixin class for Client and Flow"""

    def post(
        self,
        on: str,
        inputs: Optional['InputType'] = None,
        on_done: Optional['CallbackFnType'] = None,
        on_error: Optional['CallbackFnType'] = None,
        on_always: Optional['CallbackFnType'] = None,
        parameters: Optional[Dict] = None,
        target_executor: Optional[str] = None,
        request_size: int = 100,
        show_progress: bool = False,
        continue_on_error: bool = False,
        return_results: bool = False,
        **kwargs,
    ) -> Optional[Union['DocumentArray', List['Response']]]:
        """Post a general data request to the Flow.

        :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document id.
        :param on: the endpoint is used for identifying the user-defined ``request_type``, labeled by ``@requests(on='/abc')``
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is either resolved or rejected.
        :param parameters: the kwargs that will be sent to the executor
        :param target_executor: a regex string. Only matching Executors will process the request.
        :param request_size: the number of Documents per request. <=0 means all inputs in one request.
        :param show_progress: if set, client will show a progress bar on receiving every request.
        :param continue_on_error: if set, a Request that causes callback error will be logged only without blocking the further requests.
        :param return_results: if set, the Documents resulting from all Requests will be returned as a DocumentArray. This is useful when one wants process Responses in bulk instead of using callback.
        :param kwargs: additional parameters
        :return: None or DocumentArray containing all response Documents

        .. warning::
            ``target_executor`` uses ``re.match`` for checking if the pattern is matched.
             ``target_executor=='foo'`` will match both deployments with the name ``foo`` and ``foo_what_ever_suffix``.
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
                if c.args.results_as_docarray:
                    docs = [r.data.docs for r in result]
                    if len(docs) < 1:
                        return docs
                    else:
                        return docs[0].reduce_all(docs[1:])
                else:
                    return result

        if (on_always is None) and (on_done is None):
            return_results = True

        parameters = _include_results_field_in_param(parameters)

        return run_async(
            _get_results,
            inputs=inputs,
            on_done=on_done,
            on_error=on_error,
            on_always=on_always,
            exec_endpoint=on,
            target_executor=target_executor,
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
        inputs: Optional['InputType'] = None,
        on_done: Optional['CallbackFnType'] = None,
        on_error: Optional['CallbackFnType'] = None,
        on_always: Optional['CallbackFnType'] = None,
        parameters: Optional[Dict] = None,
        target_executor: Optional[str] = None,
        request_size: int = 100,
        show_progress: bool = False,
        continue_on_error: bool = False,
        **kwargs,
    ) -> AsyncGenerator[None, 'Response']:
        """Post a general data request to the Flow.

        :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document id.
        :param on: the endpoint is used for identifying the user-defined ``request_type``, labeled by ``@requests(on='/abc')``
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is  is either resolved or rejected.
        :param parameters: the kwargs that will be sent to the executor
        :param target_executor: a regex string. Only matching Executors will process the request.
        :param request_size: the number of Documents per request. <=0 means all inputs in one request.
        :param show_progress: if set, client will show a progress bar on receiving every request.
        :param continue_on_error: if set, a Request that causes callback error will be logged only without blocking the further requests.
        :param kwargs: additional parameters
        :yield: Response object
        """
        c = self.client
        c.show_progress = show_progress
        c.continue_on_error = continue_on_error

        parameters = _include_results_field_in_param(parameters)

        async for r in c._get_results(
            inputs=inputs,
            on_done=on_done,
            on_error=on_error,
            on_always=on_always,
            exec_endpoint=on,
            target_executor=target_executor,
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
