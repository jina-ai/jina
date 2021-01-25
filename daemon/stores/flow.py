import uuid
from typing import List, Optional, BinaryIO

from jina.flow import Flow
from jina.helper import colored, random_uuid
from .base import BaseStore
from .helper import jina_workspace


class FlowStore(BaseStore):

    def add(self, config: BinaryIO,
            workspace_id: Optional[uuid.UUID] = None,
            **kwargs):
        try:
            if not workspace_id:
                workspace_id = random_uuid()

            flow_identity = random_uuid()
            with jina_workspace(workspace_id) as _workdir:
                y_spec = config.read().decode()
                f = Flow.load_config(y_spec)
                f.identity = str(flow_identity)
                f.workspace_id = str(workspace_id)
                f.start()

        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self[flow_identity] = {
                'object': f,
                'arguments': vars(f.args),
                'yaml_source': y_spec,
                'workdir': _workdir,
                'workspace_id': workspace_id
            }
            self._logger.success(f'{colored(str(flow_identity), "cyan")} is added to workspace {colored(str(workspace_id), "cyan")}')
            return flow_identity
