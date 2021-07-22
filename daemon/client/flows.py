from typing import Dict, Union, TYPE_CHECKING

from jina.helper import run_async

from .base import BaseClient
from ..helper import if_alive


if TYPE_CHECKING:
    from ..models import DaemonID


class AsyncFlowClient(BaseClient):

    kind = 'flow'
    endpoint = '/flows'

    @if_alive
    async def create(self, *args, **kwargs) -> Dict:
        return super().create(*args, **kwargs)

    @if_alive
    async def delete(self, identity: Union[str, 'DaemonID'], *args, **kwargs) -> str:
        return super().delete(identity, *args, **kwargs)


class FlowClient(AsyncFlowClient):
    def create(self, *args, **kwargs) -> Dict:
        return run_async(super().create, *args, **kwargs)

    def delete(self, identity: Union[str, 'DaemonID'], *args, **kwargs) -> str:
        return run_async(super().delete, *args, **kwargs)
