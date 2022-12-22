import argparse
import asyncio
import urllib
from http import HTTPStatus
from typing import TYPE_CHECKING, Optional, Union

from jina.enums import GatewayProtocolType
from jina.excepts import PortAlreadyUsed
from jina.helper import is_port_free, send_telemetry_event
from jina.parsers.helper import _update_gateway_args
from jina.serve.gateway import BaseGateway
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.secrets import replace_args_with_secrets

if TYPE_CHECKING:  # pragma: no cover
    import multiprocessing
    import threading

# Keep these imports even if not used, since YAML parser needs to find them in imported modules
from jina.serve.runtimes.gateway.composite import CompositeGateway
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
        args = replace_args_with_secrets(args, getattr(args, 'secrets', []))
        self.timeout_send = args.timeout_send
        if self.timeout_send:
            self.timeout_send /= 1e3  # convert ms to seconds
        _update_gateway_args(args)
        super().__init__(args, cancel_event, **kwargs)

    async def async_setup(self):
        """
        The async method setup the runtime.

        Setup the uvicorn server.
        """
        if not (is_port_free(self.args.host, self.args.port)):
            raise PortAlreadyUsed(f'port:{self.args.port}')

        uses_with = self.args.uses_with or {}
        self.gateway = BaseGateway.load_config(
            self.args.uses,
            uses_with=dict(
                name=self.name,
                grpc_server_options=self.args.grpc_server_options,
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
            },
            py_modules=self.args.py_modules,
            extra_search_paths=self.args.extra_search_paths,
        )

        await self.gateway.setup_server()

    def _send_telemetry_event(self):
        is_custom_gateway = self.gateway.__class__ not in [
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
            self.gateway, '_should_exit', False
        ):
            await asyncio.sleep(0.1)

        await self.async_cancel()

    async def async_teardown(self):
        """Shutdown the server."""
        await self.gateway.streamer.close()
        await self.gateway.shutdown()
        await self.async_cancel()

    async def async_cancel(self):
        """Stop the server."""
        await self.gateway.streamer.close()
        await self.gateway.shutdown()

    async def async_run_forever(self):
        """Running method of the server."""
        await self.gateway.run_server()
        self.is_cancel.set()

    @staticmethod
    def is_ready(
        ctrl_address: str,
        protocol: Optional[str] = 'grpc',
        timeout: float = 1.0,
        **kwargs,
    ) -> bool:
        """
        Check if status is ready.

        :param ctrl_address: the address where the control request needs to be sent
        :param protocol: protocol of the gateway runtime
        :param timeout: timeout of grpc call in seconds
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
                conn = urllib.request.urlopen(
                    url=f'http://{ctrl_address}', timeout=timeout
                )
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
