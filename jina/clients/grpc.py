from .base import BaseClient
from .mixin import PostMixin


class GRPCClient(PostMixin, BaseClient):
    """A simple Python client for connecting to the gRPC gateway.

    It manages the asyncio event loop internally, so all interfaces are synchronous from the outside.
    """

    @property
    def client(self) -> 'GRPCClient':
        """Return the client object itself
        .. # noqa: DAR201"""
        return self
