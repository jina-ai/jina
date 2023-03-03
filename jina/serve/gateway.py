from types import SimpleNamespace
from typing import Dict, Optional

from jina.jaml import JAMLCompatible
from jina.serve.runtimes.servers import BaseServer
from jina.serve.helper import store_init_kwargs, wrap_func
from jina.serve.runtimes.gateway.request_handling import GatewayRequestHandler

__all__ = ['BaseGateway']


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


class BaseGateway(BaseServer, JAMLCompatible, metaclass=GatewayType):
    """
    The base class of all custom Gateways, can be used to build a custom interface to a Jina Flow that supports
    gateway logic

    :class:`jina.Gateway` as an alias for this class.
    """

    def __init__(self, name: Optional[str] = 'gateway', runtime_args: Optional[Dict] = None, **kwargs):
        """
        :param name: Gateway pod name
        :param runtime_args: a dict of arguments injected from :class:`Runtime` during runtime
        :param kwargs: additional extra keyword arguments to avoid failing when extra params ara passed that are not expected
        """
        super().__init__(name, runtime_args, **kwargs)
        self._add_gateway_args()
        self.tracing = self.runtime_args.tracing
        self.tracer_provider = self.runtime_args.tracer_provider
        self.grpc_tracing_server_interceptors = (
            self.runtime_args.grpc_tracing_server_interceptors
        )
        self._request_handler = GatewayRequestHandler(
            args=self.runtime_args,
            logger=self.logger,
        )
        self.streamer = self._request_handler.streamer  # backward compatibility
        self.executor = self._request_handler.executor  # backward compatibility

    def _add_gateway_args(self):
        from jina.parsers import set_gateway_runtime_args_parser

        parser = set_gateway_runtime_args_parser()
        default_args = parser.parse_args([])
        default_args_dict = dict(vars(default_args))
        _runtime_args = self.runtime_args or {}
        runtime_set_args = {
            'tracer_provider': None,
            'grpc_tracing_server_interceptors': None,
            'runtime_name': 'test',
            'metrics_registry': None,
            'meter': None,
            'aio_tracing_client_interceptors': None,
            'tracing_client_interceptor': None,
        }
        runtime_args_dict = {**runtime_set_args, **default_args_dict, **_runtime_args}
        self.runtime_args = SimpleNamespace(**runtime_args_dict)
