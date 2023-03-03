import signal
import threading
import time
import argparse
import asyncio

from jina.logging.logger import JinaLogger
from jina.constants import __windows__
from jina.serve.instrumentation import InstrumentationMixin
from jina.serve.runtimes.monitoring import MonitoringMixin
from jina.excepts import RuntimeTerminated

from typing import TYPE_CHECKING, Optional, Union

from jina.excepts import PortAlreadyUsed
from jina.helper import ArgNamespace, is_port_free, send_telemetry_event
from jina.parsers import set_gateway_parser
from jina.parsers.helper import _update_gateway_args
from jina.serve.gateway import BaseGateway

# Keep these imports even if not used, since YAML parser needs to find them in imported modules
from jina.serve.runtimes.gateway.composite import CompositeGateway
from jina.serve.runtimes.gateway.grpc import GRPCGateway
from jina.serve.runtimes.gateway.http import HTTPGateway
from jina.serve.runtimes.gateway.websocket import WebSocketGateway


if TYPE_CHECKING:  # pragma: no cover
    import multiprocessing

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
    signal.SIGSEGV,
)


class AsyncNewLoopRuntime(MonitoringMixin, InstrumentationMixin):
    """
    Runtime to make sure that a server can asynchronously run inside a new asynchronous loop. It will make sure that the server is run forever while handling the TERMINATE signals
    to be received by the orchestrator to shutdown the server and its resources.
    """

    def __init__(
            self,
            args: 'argparse.Namespace',
            cancel_event: Optional[
                Union['asyncio.Event', 'multiprocessing.Event', 'threading.Event']
            ] = None,
            req_handler_class_name: str = 'GatewayRequestHandler',
            **kwargs,
    ):
        self.timeout_send = args.timeout_send
        if self.timeout_send:
            self.timeout_send /= 1e3  # convert ms to seconds
        _update_gateway_args(args)
        self.args = args
        if args.name:
            self.name = f'{args.name}/{self.__class__.__name__}'
        else:
            self.name = self.__class__.__name__
        self.logger = JinaLogger(self.name, **vars(self.args))
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self.is_cancel = cancel_event or asyncio.Event()

        if not __windows__:

            def _cancel(sig):
                def _inner_cancel(*args, **kwargs):
                    self.logger.debug(f'Received signal {sig.name}')
                    self.is_cancel.set(),

                return _inner_cancel

            for sig in HANDLED_SIGNALS:
                self._loop.add_signal_handler(sig, _cancel(sig), sig, None)
        else:

            def _cancel(signum, frame):
                self.logger.debug(f'Received signal {signum}')
                self.is_cancel.set(),

            for sig in HANDLED_SIGNALS:
                signal.signal(sig, _cancel)

        self._setup_monitoring()
        self._setup_instrumentation(
            name=self.args.name,
            tracing=self.args.tracing,
            traces_exporter_host=self.args.traces_exporter_host,
            traces_exporter_port=self.args.traces_exporter_port,
            metrics=self.args.metrics,
            metrics_exporter_host=self.args.metrics_exporter_host,
            metrics_exporter_port=self.args.metrics_exporter_port,
        )
        self._start_time = time.time()
        self._loop.run_until_complete(self.async_setup())
        self._send_telemetry_event()

    def _send_telemetry_event(self):
        send_telemetry_event(event='start', obj=self, entity_id=self._entity_id)

    def run_forever(self):
        """
        Running method to block the main thread.

        Run the event loop until a Future is done.
        """
        self._loop.run_until_complete(self._loop_body())

    def _teardown_instrumentation(self):
        try:
            if self.tracing and self.tracer_provider:
                if hasattr(self.tracer_provider, 'force_flush'):
                    self.tracer_provider.force_flush()
                if hasattr(self.tracer_provider, 'shutdown'):
                    self.tracer_provider.shutdown()
            if self.metrics and self.meter_provider:
                if hasattr(self.meter_provider, 'force_flush'):
                    self.meter_provider.force_flush()
                if hasattr(self.meter_provider, 'shutdown'):
                    self.meter_provider.shutdown()
        except Exception as ex:
            self.logger.warning(f'Exception during instrumentation teardown, {str(ex)}')

    def teardown(self):
        """Call async_teardown() and stop and close the event loop."""
        self._teardown_instrumentation()
        self._loop.run_until_complete(self.async_teardown())
        self._loop.stop()
        self._loop.close()
        self.logger.close()
        self._stop_time = time.time()
        send_telemetry_event(
            event='stop',
            obj=self,
            duration=self._stop_time - self._start_time,
            entity_id=self._entity_id,
        )

    async def _wait_for_cancel(self):
        """Do NOT override this method when inheriting from :class:`GatewayPod`"""
        # threads are not using asyncio.Event, but threading.Event
        if isinstance(self.is_cancel, asyncio.Event):
            await self.is_cancel.wait()
        else:
            while not self.is_cancel.is_set():
                await asyncio.sleep(0.1)

        await self.async_cancel()

    async def _loop_body(self):
        """Do NOT override this method when inheriting from :class:`GatewayPod`"""
        try:
            await asyncio.gather(self.async_run_forever(), self._wait_for_cancel())
        except asyncio.CancelledError:
            self.logger.warning('received terminate ctrl message from main process')

    def _cancel(self):
        """
        Signal the runtime to terminate
        """
        self.is_cancel.set()

    async def async_setup(self):
        """
        The async method setup the runtime.

        Setup the uvicorn server.
        """
        if not (is_port_free(self.args.host, self.args.port)):
            raise PortAlreadyUsed(f'port:{self.args.port}')

        # consturct server type based on protocol (and potentially req handler class to keep backwards compatibility
        uses_with = self.args.uses_with or {}
        non_defaults = ArgNamespace.get_non_defaults_args(
            self.args, set_gateway_parser()
        )
        self.server = BaseGateway.load_config(
            self.args.uses,
            uses_with=dict(
                **non_defaults,
                **uses_with,
            ),
            uses_metas={},
            runtime_args={  # these are not parsed to the yaml config file but are pass directly during init
                'name': self.args.name,
                'port': self.args.port,
                'protocol': self.args.protocol,
                'host': self.args.host,
                'tracing': self.tracing,
                'tracer_provider': self.tracer_provider,
                'grpc_tracing_server_interceptors': self.aio_tracing_server_interceptors(),
                'graph_description': self.args.graph_description,
                'graph_conditions': self.args.graph_conditions,
                'deployments_addresses': self.args.deployments_addresses,
                'deployments_metadata': self.args.deployments_metadata,
                'deployments_no_reduce': self.args.deployments_no_reduce,
                'timeout_send': self.timeout_send,
                'retries': self.args.retries,
                'compression': self.args.compression,
                'runtime_name': self.args.name,
                'prefetch': self.args.prefetch,
                'metrics_registry': self.metrics_registry,
                'meter': self.meter,
                'aio_tracing_client_interceptors': self.aio_tracing_client_interceptors(),
                'tracing_client_interceptor': self.tracing_client_interceptor(),
                'log_config': self.args.log_config,
                'default_port': getattr(self.args, 'default_port', False),
            },
            py_modules=self.args.py_modules,
            extra_search_paths=self.args.extra_search_paths,
        )

        await self.server.setup_server()

    def _send_telemetry_event(self):
        is_custom_gateway = self.server.__class__ not in [
            CompositeGateway,
            GRPCGateway,
            HTTPGateway,
            WebSocketGateway,
        ]
        send_telemetry_event(
            event='start',
            obj=self,
            entity_id=self._entity_id,
            is_custom_gateway=is_custom_gateway,
            protocol=self.args.protocol,
        )

    async def _wait_for_cancel(self):
        """Do NOT override this method when inheriting from :class:`GatewayPod`"""
        # handle terminate signals
        while not self.is_cancel.is_set() and not getattr(
                self.server, '_should_exit', False
        ):
            await asyncio.sleep(0.1)

        await self.async_cancel()

    async def async_teardown(self):
        """Shutdown the server."""
        await self.server.shutdown()
        await self.async_cancel()

    async def async_cancel(self):
        """Stop the server."""
        await self.server.shutdown()

    async def async_run_forever(self):
        """Running method of the server."""
        self.warmup_task = asyncio.create_task(
            self.gateway.streamer.warmup(self.warmup_stop_event)
        )
        await self.server.run_server()
        self.is_cancel.set()

    @property
    def _entity_id(self):
        import uuid

        if hasattr(self, '_entity_id_'):
            return self._entity_id_
        self._entity_id_ = uuid.uuid1().hex
        return self._entity_id_

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type == RuntimeTerminated:
            self.logger.debug(f'{self!r} is ended')
        elif exc_type == KeyboardInterrupt:
            self.logger.debug(f'{self!r} is interrupted by user')
        elif exc_type and issubclass(exc_type, Exception):
            self.logger.error(
                f'{exc_val!r} during {self.run_forever!r}'
                + f'\n add "--quiet-error" to suppress the exception details'
                if not self.args.quiet_error
                else '',
                exc_info=not self.args.quiet_error,
            )
        try:
            self.teardown()
        except OSError:
            # OSError(Stream is closed) already
            pass
        except Exception as ex:
            self.logger.error(
                f'{ex!r} during {self.teardown!r}'
                + f'\n add "--quiet-error" to suppress the exception details'
                if not self.args.quiet_error
                else '',
                exc_info=not self.args.quiet_error,
            )

        # https://stackoverflow.com/a/28158006
        # return True will silent all exception stack trace here, silence is desired here as otherwise it is too
        # noisy
        #
        # doc: If an exception is supplied, and the method wishes to suppress the exception (i.e., prevent it
        # from being propagated), it should return a true value. Otherwise, the exception will be processed normally
        # upon exit from this method.
        return True
