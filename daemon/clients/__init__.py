from typing import Optional, Dict, TYPE_CHECKING, Union, Awaitable

from jina.logging.logger import JinaLogger

from .base import BaseClient, AsyncBaseClient
from .peas import PeaClient, AsyncPeaClient
from .pods import PodClient, AsyncPodClient
from .flows import FlowClient, AsyncFlowClient
from .workspaces import WorkspaceClient, AsyncWorkspaceClient


__all__ = ['JinaDClient', 'AsyncJinaDClient']


if TYPE_CHECKING:
    from ..models.id import DaemonID


class JinaDClient:
    """JinaD Client

    :param host: hostname of remote JinaD server
    :param port: port of remote JinaD server
    :param timeout: default timeout for requests, defaults to None
    """

    base_cls = BaseClient
    pea_cls = PeaClient
    pod_cls = PodClient
    flow_cls = FlowClient
    workspace_cls = WorkspaceClient

    def __init__(self, host: str, port: int, timeout: int = None) -> None:
        uri = f'{host}:{port}'
        timeout = timeout
        logger = JinaLogger(self.__class__.__name__)
        self.kwargs = {'uri': uri, 'logger': logger, 'timeout': timeout}

    @property
    def peas(self):
        """Pea Client

        :return: Pea Client
        """
        return self.pea_cls(**self.kwargs)

    @property
    def pods(self) -> Union[PodClient, AsyncPodClient]:
        """Pod Client

        :return: Pod Client
        """
        return self.pod_cls(**self.kwargs)

    @property
    def flows(self) -> Union[FlowClient, AsyncFlowClient]:
        """Flow Client

        :return: Flow Client
        """
        return self.flow_cls(**self.kwargs)

    @property
    def workspaces(self) -> Union[WorkspaceClient, AsyncWorkspaceClient]:
        """Workspace Client

        :return: Workspace Client
        """
        return self.workspace_cls(**self.kwargs)

    @property
    def alive(self) -> bool:
        """Check if JinaD is alive

        :return: True if alive
        """
        return self.base_cls(**self.kwargs).alive()

    @property
    def status(self) -> Optional[Dict]:
        """Get the status of remote JinaD

        :return: Dict object describing remote store
        """
        return self.base_cls(**self.kwargs).status()


class AsyncJinaDClient(JinaDClient):
    """Async JinaD Client"""

    base_cls = AsyncBaseClient
    pea_cls = AsyncPeaClient
    pod_cls = AsyncPodClient
    flow_cls = AsyncFlowClient
    workspace_cls = AsyncWorkspaceClient

    @property
    async def logs(self, id: 'DaemonID') -> Awaitable:
        """Stream logs

        :param identity: id of the JinaD object
        :return: logs coroutine to be awaited
        """
        return await self.base_cls(**self.kwargs).logstream(id=id)
