import signal
import threading
import time
import argparse
import asyncio

from jina.logging.logger import JinaLogger
from jina.constants import __windows__
from jina.excepts import RuntimeTerminated

from typing import TYPE_CHECKING, Optional, Union

from jina.excepts import PortAlreadyUsed
from jina.helper import ArgNamespace, is_port_free, send_telemetry_event
from jina.parsers import set_gateway_parser
from jina.parsers.helper import _set_gateway_uses
from jina.serve.runtimes.gateway.gateway import BaseGateway

# Keep these imports even if not used, since YAML parser needs to find them in imported modules
from jina.serve.runtimes.gateway.composite import CompositeGateway
from jina.serve.runtimes.gateway.grpc import GRPCGateway
from jina.serve.runtimes.gateway.http import HTTPGateway
from jina.serve.runtimes.gateway.websocket import WebSocketGateway
from jina.helper import random_ports

if TYPE_CHECKING:  # pragma: no cover
    import multiprocessing

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
    signal.SIGSEGV,
)


class AsyncNewLoopRuntime:
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
            req_handler_cls=None,
            **kwargs,
    ):
        self.req_handler_cls = req_handler_cls
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

    def teardown(self):
        """Call async_teardown() and stop and close the event loop."""
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
        if isinstance(self.is_cancel, asyncio.Event) and not hasattr(self.server, '_should_exit'):
            await self.is_cancel.wait()
        else:
            while not self.is_cancel.is_set() and not getattr(
                    self.server, '_should_exit', False
            ):
                await asyncio.sleep(0.1)

        await self.async_teardown()

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

    def _get_server(self):
        # construct server type based on protocol (and potentially req handler class to keep backwards compatibility)
        if self.req_handler_cls.__name__ == 'GatewayRequestHandler':
            self.timeout_send = self.args.timeout_send
            if self.timeout_send:
                self.timeout_send /= 1e3  # convert ms to seconds
            if not self.args.port:
                self.args.port = random_ports(len(self.args.protocol))
            _set_gateway_uses(self.args)
            uses_with = self.args.uses_with or {}
            non_defaults = ArgNamespace.get_non_defaults_args(
                self.args, set_gateway_parser()
            )
            if 'title' not in non_defaults:
                uses_with['title'] = self.args.title
            if 'description' not in non_defaults:
                uses_with['description'] = self.args.description
            if 'no_debug_endpoints' not in non_defaults:
                uses_with['no_debug_endpoints'] = self.args.no_debug_endpoints
            if 'no_crud_endpoints' not in non_defaults:
                uses_with['no_crud_endpoints'] = self.args.no_crud_endpoints
            if 'expose_endpoints' not in non_defaults:
                uses_with['expose_endpoints'] = self.args.expose_endpoints
            if 'expose_graphql_endpoint' not in non_defaults:
                uses_with['expose_graphql_endpoint'] = self.args.expose_graphql_endpoint
            if 'cors' not in non_defaults:
                uses_with['cors'] = self.args.cors
            return BaseGateway.load_config(
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
                    'log_config': self.args.log_config,
                    'default_port': getattr(self.args, 'default_port', False),
                },
                py_modules=self.args.py_modules,
                extra_search_paths=self.args.extra_search_paths,
            )

        elif not hasattr(self.args, 'protocol') or (len(self.args.protocol) == 1 and self.args.protocol[0] == 'GRPC'):
            from jina.serve.runtimes.servers.grpc import GRPCServer
            return GRPCServer(name=self.args.name,
                              runtime_args=self.args,
                              req_handler_cls=self.req_handler_cls,
                              grpc_server_options=self.args.grpc_server_options,
                              ssl_keyfile=getattr(self.args, 'ssl_keyfile', None),
                              ssl_certfile=getattr(self.args, 'ssl_certfile', None))

    def _send_telemetry_event(self):
        pass
        # is_custom_gateway = self.server.__class__ not in [
        #     CompositeGateway,
        #     GRPCGateway,
        #     HTTPGateway,
        #     WebSocketGateway,
        # ]
        # send_telemetry_event(
        #     event='start',
        #     obj=self,
        #     entity_id=self._entity_id,
        #     is_custom_gateway=is_custom_gateway,
        #     protocol=self.args.protocol,
        # )

    async def async_setup(self):
        """
        The async method setup the runtime.

        Setup the uvicorn server.
        """
        if not (is_port_free(self.args.host, self.args.port)):
            raise PortAlreadyUsed(f'port:{self.args.port}')

        self.server = self._get_server()

        await self.server.setup_server()

    async def async_teardown(self):
        """Shutdown the server."""
        await self.server.shutdown()

    async def async_run_forever(self):
        """Running method of the server."""
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
