import argparse
import asyncio
import urllib
from http import HTTPStatus
from typing import TYPE_CHECKING, Optional, Union

from jina import __default_host__
from jina.enums import GatewayProtocolType
from jina.excepts import PortAlreadyUsed
from jina.helper import is_port_free
from jina.parsers.helper import _set_gateway_uses
from jina.serve.gateway import BaseGateway
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime

if TYPE_CHECKING: # pragma: no cover
    import multiprocessing
    import threading


# Keep these imports even if not used, since YAML parser needs to find them in imported modules
from jina.serve.runtimes.gateway.grpc import GRPCGateway
from jina.serve.runtimes.gateway.http import HTTPGateway
from jina.serve.runtimes.gateway.websocket import WebSocketGateway


class GatewayRuntime(AsyncNewLoopRuntime):
    """
    The Gateway Runtime that starts a gateway pod.
    The GatewayRuntime is associated with a Gateway class that inherits :class:`~BaseGateway`.
    While the Gateway class takes care of server and application logic and serving gRPC/HTTP/Websocket API,
    The GatewayRuntime is responsible of instantiating the right Gateway class, injecting right parameters to it and
    running/terminating the Gateway object.
    """

    def __init__(
        self,
        args: argparse.Namespace,
        cancel_event: Optional[
            Union['asyncio.Event', 'multiprocessing.Event', 'threading.Event']
        ] = None,
        **kwargs,
    ):
        # this order is intentional: The timeout is needed in _create_topology_graph(), called by super
        self.timeout_send = args.timeout_send
        if self.timeout_send:
            self.timeout_send /= 1e3  # convert ms to seconds
        _set_gateway_uses(args)
        super().__init__(args, cancel_event, **kwargs)

    async def async_setup(self):
        """
        The async method setup the runtime.

        Setup the uvicorn server.
        """
        if not (is_port_free(__default_host__, self.args.port)):
            raise PortAlreadyUsed(f'port:{self.args.port}')

        uses_with = self.args.uses_with or {}
        self.gateway = BaseGateway.load_config(
            self.args.uses,
            uses_with=dict(
                name=self.name,
                grpc_server_options=self.args.grpc_server_options,
                port=self.args.port,
                title=self.args.title,
                description=self.args.description,
                no_debug_endpoints=self.args.no_debug_endpoints,
                no_crud_endpoints=self.args.no_crud_endpoints,
                expose_endpoints=self.args.expose_endpoints,
                expose_graphql_endpoint=self.args.expose_graphql_endpoint,
                cors=self.args.cors,
                ssl_keyfile=self.args.ssl_keyfile,
                ssl_certfile=self.args.ssl_certfile,
                uvicorn_kwargs=self.args.uvicorn_kwargs,
                proxy=self.args.proxy,
                **uses_with,
            ),
            uses_metas={},
            runtime_args={  # these are not parsed to the yaml config file but are pass directly during init
                'name': self.args.name,
            },
            py_modules=self.args.py_modules,
            extra_search_paths=self.args.extra_search_paths,
        )

        self.gateway.inject_dependencies(
            args=self.args,
            timeout_send=self.timeout_send,
            metrics_registry=self.metrics_registry,
            meter=self.meter,
            runtime_name=self.args.name,
            tracing=self.tracing,
            tracer_provider=self.tracer_provider,
            grpc_tracing_server_interceptors=self.aio_tracing_server_interceptors(),
            aio_tracing_client_interceptors=self.aio_tracing_client_interceptors(),
            tracing_client_interceptor=self.tracing_client_interceptor(),
        )
        await self.gateway.setup_server()

    async def _wait_for_cancel(self):
        """Do NOT override this method when inheriting from :class:`GatewayPod`"""
        # handle terminate signals
        while not self.is_cancel.is_set() and not self.gateway.should_exit:
            await asyncio.sleep(0.1)

        await self.async_cancel()

    async def async_teardown(self):
        """Shutdown the server."""
        await self.gateway.teardown()
        await self.async_cancel()

    async def async_cancel(self):
        """Stop the server."""
        await self.gateway.stop_server()

    async def async_run_forever(self):
        """Running method of the server."""
        await self.gateway.run_server()

    @staticmethod
    def is_ready(ctrl_address: str, protocol: Optional[str] = 'grpc', **kwargs) -> bool:
        """
        Check if status is ready.

        :param ctrl_address: the address where the control request needs to be sent
        :param protocol: protocol of the gateway runtime
        :param kwargs: extra keyword arguments

        :return: True if status is ready else False.
        """

        if (
            protocol is None
            or protocol == GatewayProtocolType.GRPC
            or protocol == 'grpc'
        ):
            res = AsyncNewLoopRuntime.is_ready(ctrl_address)
        else:
            try:
                conn = urllib.request.urlopen(url=f'http://{ctrl_address}')
                res = conn.code == HTTPStatus.OK
            except:
                res = False
        return res

    @classmethod
    def wait_for_ready_or_shutdown(
        cls,
        timeout: Optional[float],
        ready_or_shutdown_event: Union['multiprocessing.Event', 'threading.Event'],
        ctrl_address: str,
        protocol: Optional[str] = 'grpc',
        **kwargs,
    ):
        """
        Check if the runtime has successfully started

        :param timeout: The time to wait before readiness or failure is determined
        :param ctrl_address: the address where the control message needs to be sent
        :param ready_or_shutdown_event: the multiprocessing event to detect if the process failed or is ready
        :param protocol: protocol of the gateway runtime
        :param kwargs: extra keyword arguments

        :return: True if is ready or it needs to be shutdown
        """
        return super().wait_for_ready_or_shutdown(
            timeout=timeout,
            ready_or_shutdown_event=ready_or_shutdown_event,
            ctrl_address=ctrl_address,
            protocol=protocol,
        )
