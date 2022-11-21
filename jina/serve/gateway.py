import abc
import argparse
from typing import TYPE_CHECKING, Dict, Optional, Sequence

from jina.jaml import JAMLCompatible
from jina.logging.logger import JinaLogger
from jina.serve.helper import store_init_kwargs, wrap_func

__all__ = ['BaseGateway']

if TYPE_CHECKING:  # pragma: no cover
    from grpc.aio._interceptor import ClientInterceptor, ServerInterceptor
    from opentelemetry import trace
    from opentelemetry.instrumentation.grpc._client import (
        OpenTelemetryClientInterceptor,
    )
    from opentelemetry.metrics import Meter
    from prometheus_client import CollectorRegistry


class GatewayType(type(JAMLCompatible), type):
    """The class of Gateway type, which is the metaclass of :class:`BaseGateway`."""

    def __new__(cls, *args, **kwargs):
        """
        # noqa: DAR101
        # noqa: DAR102

        :return: Gateway class
        """
        _cls = super().__new__(cls, *args, **kwargs)
        return cls.register_class(_cls)

    @staticmethod
    def register_class(cls):
        """
        Register a class.

        :param cls: The class.
        :return: The class, after being registered.
        """

        reg_cls_set = getattr(cls, '_registered_class', set())

        cls_id = f'{cls.__module__}.{cls.__name__}'
        if cls_id not in reg_cls_set:
            reg_cls_set.add(cls_id)
            setattr(cls, '_registered_class', reg_cls_set)
            wrap_func(
                cls,
                ['__init__'],
                store_init_kwargs,
                taboo={'self', 'args', 'kwargs', 'runtime_args'},
            )
        return cls


class BaseGateway(JAMLCompatible, metaclass=GatewayType):
    """
    The base class of all custom Gateways, can be used to build a custom interface to a Jina Flow that supports
    gateway logic

    :class:`jina.Gateway` as an alias for this class.
    """

    def __init__(
        self,
        name: Optional[str] = 'gateway',
        runtime_args: Optional[Dict] = None,
        **kwargs,
    ):
        """
        :param name: Gateway pod name
        :param runtime_args: a dict of arguments injected from :class:`Runtime` during runtime
        :param kwargs: additional extra keyword arguments to avoid failing when extra params ara passed that are not expected
        """
        self._add_runtime_args(runtime_args)
        self.name = name
        self.logger = JinaLogger(self.name)
        self.tracing = self.runtime_args.tracing
        self.tracer_provider = self.runtime_args.tracer_provider
        self.grpc_tracing_server_interceptors = (
            self.runtime_args.grpc_tracing_server_interceptors
        )

        import json

        from jina.serve.streamer import GatewayStreamer

        graph_description = json.loads(self.runtime_args.graph_description)
        graph_conditions = json.loads(self.runtime_args.graph_conditions)
        deployments_addresses = json.loads(self.runtime_args.deployments_addresses)
        deployments_metadata = json.loads(self.runtime_args.deployments_metadata)
        deployments_no_reduce = json.loads(self.runtime_args.deployments_no_reduce)

        self.streamer = GatewayStreamer(
            graph_representation=graph_description,
            executor_addresses=deployments_addresses,
            graph_conditions=graph_conditions,
            deployments_metadata=deployments_metadata,
            deployments_no_reduce=deployments_no_reduce,
            timeout_send=self.runtime_args.timeout_send,
            retries=self.runtime_args.retries,
            compression=self.runtime_args.compression,
            runtime_name=self.runtime_args.runtime_name,
            prefetch=self.runtime_args.prefetch,
            logger=self.logger,
            metrics_registry=self.runtime_args.metrics_registry,
            meter=self.runtime_args.meter,
            aio_tracing_client_interceptors=self.runtime_args.aio_tracing_client_interceptors,
            tracing_client_interceptor=self.runtime_args.tracing_client_interceptor,
        )

    @abc.abstractmethod
    async def setup_server(self):
        """Setup server"""
        ...

    @abc.abstractmethod
    async def run_server(self):
        """Run server forever"""
        ...

    @abc.abstractmethod
    async def shutdown(self):
        """Shutdown the server and free other allocated resources, e.g, streamer object, health check service, ..."""
        ...

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _set_single_port_protocol(self):
        if len(self.runtime_args.port) < 1 or len(self.runtime_args.protocol) < 1:
            raise ValueError(f'{self.__class__} expects at least 1 port and 1 protcol')
        self.port = self.runtime_args.port[0]
