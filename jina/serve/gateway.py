import abc
import argparse
from typing import TYPE_CHECKING, Optional

from jina.jaml import JAMLCompatible
from jina.logging.logger import JinaLogger
from jina.serve.streamer import GatewayStreamer

__all__ = ['BaseGateway']


class BaseGateway(JAMLCompatible):
    """
    The base class of all custom Gateways, can be used to build a custom interface to a Jina Flow that supports
    gateway logic

    :class:`jina.Gateway` as an alias for this class.
    """

    def __init__(
        self,
        streamer: Optional[GatewayStreamer] = None,
        args: 'argparse.Namespace' = None,
        logger: 'JinaLogger' = None,
        **kwargs,
    ):
        """
        :param streamer: configured gateway streamer
        :param args: args
        :param logger: jina logger object
        :param kwargs: additional extra keyword arguments to avoid failing when extra params ara passed that are not expected
        """
        self.streamer = streamer
        self.args = args
        self.logger = logger
        self.app = self.get_app()

    @abc.abstractmethod
    def get_app(self):
        """Initialize and return ASGI application"""
        pass

    def stop(self):
        """Stop ASGI application"""
        pass
