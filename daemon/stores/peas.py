from typing import TYPE_CHECKING, Union

from jina.helper import ArgNamespace
from .containers import ContainerStore
from ..models import DaemonID

if TYPE_CHECKING:
    from ..models import PeaModel, PodModel


class PeaStore(ContainerStore):

    _kind = 'pea'

    @property
    def command(self) -> str:
        return f'jina {self._kind} {" ".join(ArgNamespace.kwargs2list(self.params.dict(exclude={"log_config"})))}'

    def add(self,
            workspace_id: DaemonID,
            model: Union['PeaModel', 'PodModel'],
            *args,
            **kwargs):
        """[summary]

        :param workspace_id: [description]
        :type workspace_id: DaemonID
        :param model: [description]
        :type model: Union[
        :return: [description]
        :rtype: [type]
        """
        id = DaemonID('jpea')
        self.params = model
        return super().add(id=id, workspace_id=workspace_id)
