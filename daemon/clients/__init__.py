from typing import Optional, Dict, TYPE_CHECKING, Union

from jina.logging.logger import JinaLogger

from daemon.clients.base import BaseClient, AsyncBaseClient
from daemon.clients.pods import PodClient, AsyncPodClient
from daemon.clients.deployments import DeploymentClient, AsyncDeploymentClient
from daemon.clients.flows import FlowClient, AsyncFlowClient
from daemon.clients.workspaces import WorkspaceClient, AsyncWorkspaceClient


__all__ = ['JinaDClient', 'AsyncJinaDClient']


if TYPE_CHECKING:
    from ..models.id import DaemonID


class JinaDClient:
    """JinaD Client

    :param host: hostname of remote JinaD server
    :param port: port of remote JinaD server
    :param timeout: default timeout for requests, defaults to None
    """

    _base_cls = BaseClient
    _pod_cls = PodClient
    _deployment_cls = DeploymentClient
    _flow_cls = FlowClient
    _workspace_cls = WorkspaceClient

    def __init__(
        self,
        host: str,
        port: int,
        timeout: Optional[float] = None,
        logger: JinaLogger = None,
    ) -> None:
        uri = f'{host}:{port}'
        timeout = timeout
        logger = logger or JinaLogger(self.__class__.__name__)
        self.kwargs = {'uri': uri, 'logger': logger, 'timeout': timeout}

    @property
    def pods(self):
        """Pod Client

        :return: Pod Client
        """
        return self._pod_cls(**self.kwargs)

    @property
    def deployments(self) -> Union[DeploymentClient, AsyncDeploymentClient]:
        """Deployment Client

        :return: Deployment Client
        """
        return self._deployment_cls(**self.kwargs)

    @property
    def flows(self) -> Union[FlowClient, AsyncFlowClient]:
        """Flow Client

        :return: Flow Client
        """
        return self._flow_cls(**self.kwargs)

    @property
    def workspaces(self) -> Union[WorkspaceClient, AsyncWorkspaceClient]:
        """Workspace Client

        :return: Workspace Client
        """
        return self._workspace_cls(**self.kwargs)

    @property
    def alive(self) -> bool:
        """Check if JinaD is alive

        :return: True if alive
        """
        return self._base_cls(**self.kwargs).alive()

    @property
    def status(self) -> Optional[Dict]:
        """Get the status of remote JinaD

        :return: Dict object describing remote store
        """
        return self._base_cls(**self.kwargs).status()


class AsyncJinaDClient(JinaDClient):
    """Async JinaD Client"""

    _base_cls = AsyncBaseClient
    _pod_cls = AsyncPodClient
    _deployment_cls = AsyncDeploymentClient
    _flow_cls = AsyncFlowClient
    _workspace_cls = AsyncWorkspaceClient
