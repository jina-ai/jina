import uuid
from fastapi.exceptions import HTTPException
from typing import Dict, Optional, BinaryIO

from jina.flow import Flow
from jina.helper import colored, random_uuid

from .helper import jina_workspace
from .containers import ContainerStore
from ..excepts import Runtime400Exception
from ..dockerize.helper import id_cleaner
from ..models import DaemonID, FlowModel, UpdateOperationEnum


class FlowStore(ContainerStore):
    """A Store of Flows for jinad"""
    _kind = 'flow'

    @property
    def command(self) -> str:
        return f'jina flow --uses /workspace/{self.params.uses} ' \
               f'--identity {self.params.identity} ' \
               f'--workspace-id {self.params.workspace_id}'

    def add(self,
            filename: str,
            workspace_id: DaemonID,
            *args,
            **kwargs):
        """Add a new Flow"""
        id = DaemonID('jflow')
        self.params = FlowModel(uses=filename,
                                workspace_id=workspace_id.jid,
                                identity=id.jid)
        return super().add(id=id, workspace_id=workspace_id)
