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

import grpc.aio
from opentelemetry.instrumentation.grpc._server import (
    OpenTelemetryServerInterceptor,
    _OpenTelemetryServicerContext,
    _wrap_rpc_behavior,
)


class OpenTelemetryAioServerInterceptor(
    grpc.aio.ServerInterceptor, OpenTelemetryServerInterceptor
):
    '''
    An AsyncIO gRPC server interceptor, to add OpenTelemetry.
    Usage::
        tracer = some OpenTelemetry tracer
        interceptors = [
            AsyncOpenTelemetryServerInterceptor(tracer),
        ]
        server = aio.server(
            futures.ThreadPoolExecutor(max_workers=concurrency),
            interceptors = (interceptors,))
    '''

    async def intercept_service(self, continuation, handler_call_details):
        '''
        # noqa: DAR101
        # noqa: DAR102
        # noqa: DAR201
        '''

        def telemetry_wrapper(behavior, request_streaming, response_streaming):
            # handle streaming responses specially
            if response_streaming:
                return self._intercept_aio_server_stream(
                    behavior,
                    handler_call_details,
                )

            return self._intercept_aio_server_unary(
                behavior,
                handler_call_details,
            )

        next_handler = await continuation(handler_call_details)

        return _wrap_rpc_behavior(next_handler, telemetry_wrapper)

    def _intercept_aio_server_unary(self, behavior, handler_call_details):
        async def _unary_interceptor(request_or_iterator, context):
            with self._set_remote_context(context):
                with self._start_span(
                    handler_call_details,
                    context,
                    set_status_on_exception=False,
                ) as span:
                    # wrap the context
                    context = _OpenTelemetryServicerContext(context, span)

                    # And now we run the actual RPC.
                    try:
                        return await behavior(request_or_iterator, context)

                    except Exception as error:
                        # Bare exceptions are likely to be gRPC aborts, which
                        # we handle in our context wrapper.
                        # Here, we're interested in uncaught exceptions.
                        # pylint:disable=unidiomatic-typecheck
                        if type(error) != Exception:
                            span.record_exception(error)
                        raise error

        return _unary_interceptor

    def _intercept_aio_server_stream(self, behavior, handler_call_details):
        async def _stream_interceptor(request_or_iterator, context):
            with self._set_remote_context(context):
                with self._start_span(
                    handler_call_details,
                    context,
                    set_status_on_exception=False,
                ) as span:
                    context = _OpenTelemetryServicerContext(context, span)

                    try:
                        async for response in behavior(request_or_iterator, context):
                            yield response

                    except Exception as error:
                        # pylint:disable=unidiomatic-typecheck
                        if type(error) != Exception:
                            span.record_exception(error)
                        raise error

        return _stream_interceptor
