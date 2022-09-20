# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
from collections import OrderedDict

import grpc
from grpc.aio import ClientCallDetails
from opentelemetry import context
from opentelemetry.instrumentation.grpc._client import (
    OpenTelemetryClientInterceptor,
    _carrier_setter,
)
from opentelemetry.instrumentation.utils import _SUPPRESS_INSTRUMENTATION_KEY
from opentelemetry.propagate import inject
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace.status import Status, StatusCode


def _unary_done_callback(span, code, details):
    def callback(call):
        try:
            span.set_attribute(
                SpanAttributes.RPC_GRPC_STATUS_CODE,
                code.value[0],
            )
            if code != grpc.StatusCode.OK:
                span.set_status(
                    Status(
                        status_code=StatusCode.ERROR,
                        description=details,
                    )
                )
        finally:
            span.end()

    return callback


class _BaseAioClientInterceptor(OpenTelemetryClientInterceptor):
    @staticmethod
    def propagate_trace_in_details(client_call_details):
        '''
        # noqa: DAR101
        # noqa: DAR201
        '''
        metadata = client_call_details.metadata
        if not metadata:
            mutable_metadata = OrderedDict()
        else:
            mutable_metadata = OrderedDict(metadata)

        inject(mutable_metadata, setter=_carrier_setter)
        metadata = tuple(mutable_metadata.items())

        return ClientCallDetails(
            client_call_details.method,
            client_call_details.timeout,
            metadata,
            client_call_details.credentials,
            client_call_details.wait_for_ready,
        )

    @staticmethod
    def add_error_details_to_span(span, exc):
        if isinstance(exc, grpc.RpcError):
            span.set_attribute(
                SpanAttributes.RPC_GRPC_STATUS_CODE,
                exc.code().value[0],
            )
        span.set_status(
            Status(
                status_code=StatusCode.ERROR,
                description=f"{type(exc).__name__}: {exc}",
            )
        )
        span.record_exception(exc)

    async def _wrap_unary_response(self, continuation, span):
        '''
        # noqa: DAR101
        # noqa: DAR201
        '''
        try:
            call = await continuation()

            # code and details are both coroutines that need to be await-ed,
            # the callbacks added with add_done_callback do not allow async
            # code so we need to get the code and details here then pass them
            # to the callback.
            code = await call.code()
            details = await call.details()

            call.add_done_callback(_unary_done_callback(span, code, details))

            return call
        except grpc.aio.AioRpcError as exc:
            self.add_error_details_to_span(span, exc)
            raise exc

    async def _wrap_stream_response(self, span, call):
        try:
            async for response in call:
                yield response
        except Exception as exc:
            self.add_error_details_to_span(span, exc)
            raise exc
        finally:
            span.end()


class UnaryUnaryAioClientInterceptor(
    grpc.aio.UnaryUnaryClientInterceptor,
    _BaseAioClientInterceptor,
):
    '''Affords intercepting unary-unary invocations.'''

    async def intercept_unary_unary(self, continuation, client_call_details, request):
        '''Intercepts a unary-unary invocation asynchronously.

        :param continuation: A coroutine that proceeds with the invocation by executing
            the next interceptor in the chain or invoking the actual RPC on the
            underlying Channel. It is the interceptor's responsibility to call it if
            it decides to move the RPC forward.  The interceptor can use
            `call = await continuation(client_call_details, request)` to continue with
            the RPC. `continuation` returns the call to the RPC.
        :param client_call_details: A ClientCallDetails object describing the outgoing RPC.
        :param request: The request value for the RPC.

        :returns: An object with the RPC response.

        :raises: AioRpcError: Indicating that the RPC terminated with non-OK status.
        :raises: asyncio.CancelledError: Indicating that the RPC was canceled.
        '''

        if context.get_value(_SUPPRESS_INSTRUMENTATION_KEY):
            return await continuation(client_call_details, request)

        method = client_call_details.method.decode("utf-8")
        with self._start_span(
            method,
            end_on_exit=False,
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            new_details = self.propagate_trace_in_details(client_call_details)

            continuation_with_args = functools.partial(
                continuation, new_details, request
            )
            return await self._wrap_unary_response(continuation_with_args, span)


class UnaryStreamAioClientInterceptor(
    grpc.aio.UnaryStreamClientInterceptor,
    _BaseAioClientInterceptor,
):
    '''Affords intercepting unary-stream invocations.'''

    async def intercept_unary_stream(self, continuation, client_call_details, request):
        '''Intercepts a unary-stream invocation asynchronously.

        The function could return the call object or an asynchronous
        iterator, in case of being an asyncrhonous iterator this will
        become the source of the reads done by the caller.

        :param continuation: A coroutine that proceeds with the invocation by
            executing the next interceptor in the chain or invoking the
            actual RPC on the underlying Channel. It is the interceptor's
            responsibility to call it if it decides to move the RPC forward.
            The interceptor can use
            `call = await continuation(client_call_details, request)`
            to continue with the RPC. `continuation` returns the call to the
            RPC.
        :param client_call_details: A ClientCallDetails object describing the
            outgoing RPC.
        :param request: The request value for the RPC.

        :returns: The RPC Call or an asynchronous iterator.

        :raises: AioRpcError: Indicating that the RPC terminated with non-OK status.
        :raises: asyncio.CancelledError: Indicating that the RPC was canceled.
        '''

        if context.get_value(_SUPPRESS_INSTRUMENTATION_KEY):
            return await continuation(client_call_details, request)

        method = client_call_details.method.decode("utf-8")
        with self._start_span(
            method,
            end_on_exit=False,
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            new_details = self.propagate_trace_in_details(client_call_details)

            resp = await continuation(new_details, request)

            return self._wrap_stream_response(span, resp)


class StreamUnaryAioClientInterceptor(
    grpc.aio.StreamUnaryClientInterceptor,
    _BaseAioClientInterceptor,
):
    '''Affords intercepting stream-unary invocations.'''

    async def intercept_stream_unary(
        self, continuation, client_call_details, request_iterator
    ):
        '''Intercepts a stream-unary invocation asynchronously.

        Within the interceptor the usage of the call methods like `write` or
        even awaiting the call should be done carefully, since the caller
        could be expecting an untouched call, for example for start writing
        messages to it.

        :param continuation: A coroutine that proceeds with the invocation by
            executing the next interceptor in the chain or invoking the
            actual RPC on the underlying Channel. It is the interceptor's
            responsibility to call it if it decides to move the RPC forward.
            The interceptor can use
            `call = await continuation(client_call_details, request_iterator)`
            to continue with the RPC. `continuation` returns the call to the
            RPC.
        :param client_call_details: A ClientCallDetails object describing the
            outgoing RPC.
        :param request_iterator: The request iterator that will produce requests
            for the RPC.

        :returns: The RPC Call.

        :raises: AioRpcError: Indicating that the RPC terminated with non-OK status.
        :raises: asyncio.CancelledError: Indicating that the RPC was canceled.
        '''

        if context.get_value(_SUPPRESS_INSTRUMENTATION_KEY):
            return await continuation(client_call_details, request_iterator)

        method = client_call_details.method.decode("utf-8")
        with self._start_span(
            method,
            end_on_exit=False,
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            new_details = self.propagate_trace_in_details(client_call_details)

            continuation_with_args = functools.partial(
                continuation, new_details, request_iterator
            )
            return await self._wrap_unary_response(continuation_with_args, span)


class StreamStreamAioClientInterceptor(
    grpc.aio.StreamStreamClientInterceptor,
    _BaseAioClientInterceptor,
):
    '''Affords intercepting stream-stream invocations.'''

    async def intercept_stream_stream(
        self, continuation, client_call_details, request_iterator
    ):
        '''Intercepts a stream-stream invocation asynchronously.

        Within the interceptor the usage of the call methods like `write` or
        even awaiting the call should be done carefully, since the caller
        could be expecting an untouched call, for example for start writing
        messages to it.

        The function could return the call object or an asynchronous
        iterator, in case of being an asyncrhonous iterator this will
        become the source of the reads done by the caller.

        :param continuation: A coroutine that proceeds with the invocation by
            executing the next interceptor in the chain or invoking the
            actual RPC on the underlying Channel. It is the interceptor's
            responsibility to call it if it decides to move the RPC forward.
            The interceptor can use
            `call = await continuation(client_call_details, request_iterator)`
            to continue with the RPC. `continuation` returns the call to the
            RPC.
        :param client_call_details: A ClientCallDetails object describing the
            outgoing RPC.
        :param request_iterator: The request iterator that will produce requests
            for the RPC.

        :returns: The RPC Call or an asynchronous iterator.

        :raises: AioRpcError: Indicating that the RPC terminated with non-OK status.
        :raises: asyncio.CancelledError: Indicating that the RPC was canceled.
        '''

        if context.get_value(_SUPPRESS_INSTRUMENTATION_KEY):
            return await continuation(client_call_details, request_iterator)

        method = client_call_details.method.decode("utf-8")
        with self._start_span(
            method,
            end_on_exit=False,
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            new_details = self.propagate_trace_in_details(client_call_details)

            resp = await continuation(new_details, request_iterator)

            return self._wrap_stream_response(span, resp)
