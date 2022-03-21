import warnings
from functools import partialmethod, wraps
from inspect import signature
from typing import TYPE_CHECKING, AsyncGenerator, Dict, List, Optional, Union

from jina.helper import get_or_reuse_loop, run_async
from jina.importer import ImportExtensions

if TYPE_CHECKING:
    from jina import DocumentArray
    from jina.clients.base import CallbackFnType, InputType
    from jina.types.request import Response


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


class MutateMixin:
    """The GraphQL Mutation Mixin for Client and Flow"""

    def mutate(
        self,
        mutation: str,
        variables: Optional[dict] = None,
        timeout: Optional[float] = None,
        headers: Optional[dict] = None,
    ):
        """Perform a GraphQL mutation

        :param mutation: the GraphQL mutation as a single string.
        :param variables: variables to be substituted in the mutation. Not needed if no variables are present in the mutation string.
        :param timeout: HTTP request timeout
        :param headers: HTTP headers
        :return: dict containing the optional keys ``data`` and ``errors``, for response data and errors.
        """
        with ImportExtensions(required=True):
            from sgqlc.endpoint.http import HTTPEndpoint as SgqlcHTTPEndpoint

            proto = 'https' if self.args.tls else 'http'
            graphql_url = f'{proto}://{self.args.host}:{self.args.port}/graphql'
            endpoint = SgqlcHTTPEndpoint(graphql_url)
            res = endpoint(
                mutation, variables=variables, timeout=timeout, extra_headers=headers
            )
            return res


class AsyncMutateMixin(MutateMixin):
    """The async GraphQL Mutation Mixin for Client and Flow"""

    async def mutate(
        self,
        mutation: str,
        variables: Optional[dict] = None,
        timeout: Optional[float] = None,
        headers: Optional[dict] = None,
    ):
        """Perform a GraphQL mutation, asynchronously

        :param mutation: the GraphQL mutation as a single string.
        :param variables: variables to be substituted in the mutation. Not needed if no variables are present in the mutation string.
        :param timeout: HTTP request timeout
        :param headers: HTTP headers
        :return: dict containing the optional keys ``data`` and ``errors``, for response data and errors.
        """
        return await get_or_reuse_loop().run_in_executor(
            None, super().mutate, mutation, variables, timeout, headers
        )


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
        return_responses: bool = False,
        **kwargs,
    ) -> Optional[Union['DocumentArray', List['Response']]]:
        """Post a general data request to the Flow.

        :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document.
        :param on: the endpoint which is invoked. All the functions in the executors decorated by `@requests(on=...)` with the same endpoint are invoked.
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is either resolved or rejected.
        :param parameters: the kwargs that will be sent to the executor
        :param target_executor: a regex string. Only matching Executors will process the request.
        :param request_size: the number of Documents per request. <=0 means all inputs in one request.
        :param show_progress: if set, client will show a progress bar on receiving every request.
        :param continue_on_error: if set, a Request that causes callback error will be logged only without blocking the further requests.7
        :param return_responses: if set to True, the result will come as Response and not as a `DocumentArray`

        :param kwargs: additional parameters
        :return: None or DocumentArray containing all response Documents

        .. warning::
            ``target_executor`` uses ``re.match`` for checking if the pattern is matched. ``target_executor=='foo'`` will match both deployments with the name ``foo`` and ``foo_what_ever_suffix``.
        """

        c = self.client

        if c.args.return_responses and not return_responses:
            warnings.warn(
                'return_responses was set in the Client constructor. Therefore, we are overriding the `.post()` input '
                'parameter `return_responses`. This argument will be deprecated from the `constructor` '
                'soon. We recommend passing `return_responses` to the `post` method.'
            )
            return_responses = True

        c.show_progress = show_progress
        c.continue_on_error = continue_on_error

        parameters = _include_results_field_in_param(parameters)
        on_error = _wrap_on_error(on_error) if on_error is not None else on_error

        from jina import DocumentArray

        return_results = (on_always is None) and (on_done is None)

        async def _get_results(*args, **kwargs):
            result = [] if return_responses else DocumentArray()
            async for resp in c._get_results(*args, **kwargs):
                if return_results:
                    if return_responses:
                        result.append(resp)
                    else:
                        result.extend(resp.data.docs)
            if return_results:
                return result

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
        return_responses: bool = False,
        **kwargs,
    ) -> AsyncGenerator[None, Union['DocumentArray', 'Response']]:
        """Async Post a general data request to the Flow.

        :param inputs: input data which can be an Iterable, a function which returns an Iterable, or a single Document.
        :param on: the endpoint which is invoked. All the functions in the executors decorated by `@requests(on=...)` with the same endpoint are invoked.
        :param on_done: the function to be called when the :class:`Request` object is resolved.
        :param on_error: the function to be called when the :class:`Request` object is rejected.
        :param on_always: the function to be called when the :class:`Request` object is either resolved or rejected.
        :param parameters: the kwargs that will be sent to the executor
        :param target_executor: a regex string. Only matching Executors will process the request.
        :param request_size: the number of Documents per request. <=0 means all inputs in one request.
        :param show_progress: if set, client will show a progress bar on receiving every request.
        :param continue_on_error: if set, a Request that causes callback error will be logged only without blocking the further requests.
        :param return_responses: if set to True, the result will come as Response and not as a `DocumentArray`
        :param kwargs: additional parameters
        :yield: Response object

        .. warning::
            ``target_executor`` uses ``re.match`` for checking if the pattern is matched. ``target_executor=='foo'`` will match both deployments with the name ``foo`` and ``foo_what_ever_suffix``.
        """
        c = self.client

        if c.args.return_responses and not return_responses:
            warnings.warn(
                'return_responses was set in the Client constructor. Therefore, we are overriding the `.post()` input '
                'parameter `return_responses`. This argument will be deprecated from the `constructor` '
                'soon. We recommend passing `return_responses` to the `post` method.'
            )
            return_responses = True

        c.show_progress = show_progress
        c.continue_on_error = continue_on_error

        parameters = _include_results_field_in_param(parameters)
        on_error = _wrap_on_error(on_error) if on_error is not None else on_error

        async for result in c._get_results(
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
            if not return_responses:
                yield result.data.docs
            else:
                yield result

    # ONLY CRUD, for other request please use `.post`
    index = partialmethod(post, '/index')
    search = partialmethod(post, '/search')
    update = partialmethod(post, '/update')
    delete = partialmethod(post, '/delete')


def _wrap_on_error(on_error):
    num_args = len(signature(on_error).parameters)
    if num_args == 1:
        warnings.warn(
            "on_error callback taking only the response parameters is deprecated. Please add one parameter "
            "to handle additional optional Exception as well",
            DeprecationWarning,
        )

        @wraps(on_error)
        def _fn(resp, exception):  # just skip the exception
            return on_error(resp)

        return _fn

    else:
        return on_error
