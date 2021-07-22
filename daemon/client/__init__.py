from jina.logging.logger import JinaLogger

from .peas import PeaClient
from .pods import PodClient
from .flows import FlowClient
from .workspaces import WorkspaceClient


__all__ = ['JinaDClient']


class JinaDClient:
    """[summary]

    :param host: [description]
    :param port: [description]
    :param timeout: [description], defaults to None
    :param model: [description], defaults to False
    """

    def __init__(
        self, host: str, port: int, timeout: int = None, model: bool = False
    ) -> None:
        self.uri = f'{host}:{port}'
        self.timeout = timeout
        self.model = model
        self.logger = JinaLogger(self.__class__.__name__)

    @property
    def peas(self):
        return PeaClient(uri=self.uri, logger=self.logger, timeout=self.timeout)

    @property
    def pods(self):
        return PodClient(uri=self.uri, logger=self.logger, timeout=self.timeout)

    @property
    def flows(self):
        return FlowClient(uri=self.uri, logger=self.logger, timeout=self.timeout)

    @property
    def workspaces(self):
        return WorkspaceClient(uri=self.uri, logger=self.logger, timeout=self.timeout)

    @property
    def logs(self):
        return
