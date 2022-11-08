import abc
import argparse
from typing import TYPE_CHECKING, Optional, Sequence

from jina.jaml import JAMLCompatible
from jina.logging.logger import JinaLogger
from jina.serve.helper import store_init_kwargs, wrap_func

__all__ = ['BaseGateway']

if TYPE_CHECKING: # pragma: no cover
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
                cls, ['__init__'], store_init_kwargs, taboo={'self', 'args', 'kwargs'}
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
        **kwargs,
    ):
        """
        :param name: Gateway pod name
        :param kwargs: additional extra keyword arguments to avoid failing when extra params ara passed that are not expected
        """
        self.streamer = None
        self.name = name
        # TODO: original implementation also passes args, maybe move this to a setter/initializer func
        self.logger = JinaLogger(self.name)

    def inject_dependencies(
        self,
        args: 'argparse.Namespace' = None,
        timeout_send: Optional[float] = None,
        metrics_registry: Optional['CollectorRegistry'] = None,
        meter: Optional['Meter'] = None,
        runtime_name: Optional[str] = None,
        tracing: Optional[bool] = False,
        tracer_provider: Optional['trace.TracerProvider'] = None,
        grpc_tracing_server_interceptors: Optional[
            Sequence['ServerInterceptor']
        ] = None,
        aio_tracing_client_interceptors: Optional[Sequence['ClientInterceptor']] = None,
        tracing_client_interceptor: Optional['OpenTelemetryClientInterceptor'] = None,
    ):
        """
        Set additional dependencies by providing runtime parameters.
        :param args: runtime args
        :param timeout_send: grpc connection timeout
        :param metrics_registry: metric registry when monitoring is enabled
        :param meter: optional OpenTelemetry meter that can provide instruments for collecting metrics
        :param runtime_name: name of the runtime providing the streamer
        :param tracing: Enables tracing if set to True.
        :param tracer_provider: If tracing is enabled the tracer_provider will be used to instrument the code.
        :param grpc_tracing_server_interceptors: List of async io gprc server tracing interceptors for tracing requests.
        :param aio_tracing_client_interceptors: List of async io gprc client tracing interceptors for tracing requests if asycnio is True.
        :param tracing_client_interceptor: A gprc client tracing interceptor for tracing requests if asyncio is False.
        """
        self.tracing = tracing
        self.tracer_provider = tracer_provider
        self.grpc_tracing_server_interceptors = grpc_tracing_server_interceptors
        import json

        from jina.serve.streamer import GatewayStreamer

        graph_description = json.loads(args.graph_description)
        graph_conditions = json.loads(args.graph_conditions)
        deployments_addresses = json.loads(args.deployments_addresses)
        deployments_metadata = json.loads(args.deployments_metadata)
        deployments_disable_reduce = json.loads(args.deployments_disable_reduce)

        self.streamer = GatewayStreamer(
            graph_representation=graph_description,
            executor_addresses=deployments_addresses,
            graph_conditions=graph_conditions,
            deployments_metadata=deployments_metadata,
            deployments_disable_reduce=deployments_disable_reduce,
            timeout_send=timeout_send,
            retries=args.retries,
            compression=args.compression,
            runtime_name=runtime_name,
            prefetch=args.prefetch,
            logger=self.logger,
            metrics_registry=metrics_registry,
            meter=meter,
            aio_tracing_client_interceptors=aio_tracing_client_interceptors,
            tracing_client_interceptor=tracing_client_interceptor,
        )

    @abc.abstractmethod
    async def setup_server(self):
        """Setup server"""
        ...

    @abc.abstractmethod
    async def run_server(self):
        """Run server forever"""
        ...

    async def teardown(self):
        """Free other resources allocated with the server, e.g, gateway object, ..."""
        await self.streamer.close()

    @abc.abstractmethod
    async def stop_server(self):
        """Stop server"""
        ...

    # some servers need to set a flag useful in handling termination signals
    # e.g, HTTPGateway/ WebSocketGateway
    @property
    def should_exit(self) -> bool:
        """
        Boolean flag that indicates whether the gateway server should exit or not
        :return: boolean flag
        """
        return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
