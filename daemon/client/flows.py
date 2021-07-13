from typing import Dict, Union, TYPE_CHECKING

from .base import BaseClient
from .helper import jinad_alive

if TYPE_CHECKING:
    from ..models import DaemonID


class _FlowClient(BaseClient):

    kind = 'flow'
    endpoint = '/flows'

    @jinad_alive
    def create(self, *args, **kwargs) -> Dict:
        return super().create(*args, **kwargs)

    @jinad_alive
    def delete(self, identity: Union[str, 'DaemonID'], *args, **kwargs) -> str:
        return super().delete(identity, *args, **kwargs)
