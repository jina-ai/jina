import argparse
import asyncio
import os
from typing import TYPE_CHECKING, Optional, Union

from jina import __default_host__
from jina.excepts import PortAlreadyUsed
from jina.helper import is_port_free
from jina.parsers.helper import _set_gateway_uses
from jina.serve.gateway import BaseGateway
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.gateway.grpc import GRPCGateway
from jina.serve.runtimes.gateway.http import HTTPGateway
from jina.serve.runtimes.gateway.websocket import WebSocketGateway

if TYPE_CHECKING:
    import multiprocessing
    import threading


class GatewayRuntime(AsyncNewLoopRuntime):
    # TODO: more docs here
    """
    The Gateway Runtime that starts a gateway pod.
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
        if not self.args.proxy and os.name != 'nt':
            os.unsetenv('http_proxy')
            os.unsetenv('https_proxy')

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
                **uses_with,
            ),
            uses_metas={},
            runtime_args={  # these are not parsed to the yaml config file but are pass directly during init
                'name': self.args.name,
            },
            py_modules=self.args.py_modules,
            extra_search_paths=self.args.extra_search_paths,
        )

        self.gateway.set_streamer(
            args=self.args,
            timeout_send=self.timeout_send,
            metrics_registry=self.metrics_registry,
            runtime_name=self.args.name,
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
