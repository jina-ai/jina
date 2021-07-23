from typing import Optional, Dict, TYPE_CHECKING, Union
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
    """[summary]

    :param host: [description]
    :param port: [description]
    :param timeout: [description], defaults to None
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
        return self.pea_cls(**self.kwargs)

    @property
    def pods(self) -> Union[PodClient, AsyncPodClient]:
        return self.pod_cls(**self.kwargs)

    @property
    def flows(self) -> Union[FlowClient, AsyncFlowClient]:
        return self.flow_cls(**self.kwargs)

    @property
    def workspaces(self) -> Union[WorkspaceClient, AsyncWorkspaceClient]:
        return self.workspace_cls(**self.kwargs)

    @property
    def alive(self) -> bool:
        return self.base_cls(**self.kwargs).alive()

    @property
    def status(self) -> Optional[Dict]:
        return self.base_cls(**self.kwargs).status()


class AsyncJinaDClient(JinaDClient):
    """[summary]"""

    base_cls = AsyncBaseClient
    pea_cls = AsyncPeaClient
    pod_cls = AsyncPodClient
    flow_cls = AsyncFlowClient
    workspace_cls = AsyncWorkspaceClient

    @property
    async def logs(self, identity: 'DaemonID'):
        return await self.base_cls(**self.kwargs).logstream(identity=identity)
