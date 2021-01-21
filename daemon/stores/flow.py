import uuid
from typing import Optional, BinaryIO

from jina.flow import Flow
from jina.helper import random_uuid
from .base import BaseStore
from .helper import jina_workspace


class FlowStore(BaseStore):

    def add(self, config: BinaryIO,
            workspace_id: Optional[uuid.UUID] = None,
            **kwargs):
        try:
            if not workspace_id:
                workspace_id = random_uuid()

            with jina_workspace(workspace_id) as _workdir:
                y_spec = config.read().decode()
                f = Flow.load_config(y_spec)
                f.start()

            _id = uuid.UUID(f.args.identity)
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self[_id] = {
                'object': f,
                'arguments': vars(f.args),
                'yaml_source': y_spec,
                'workdir': _workdir,
                'workspace_id': workspace_id
            }
            return _id
