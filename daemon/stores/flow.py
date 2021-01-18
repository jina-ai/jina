import os
import uuid
from pathlib import Path
from typing import Optional, BinaryIO

from jina.flow import Flow
from jina.helper import change_cwd
from .base import BaseStore
from .. import jinad_args


class FlowStore(BaseStore):

    def add(self, config: BinaryIO,
            workspace_id: Optional[uuid.UUID] = None,
            **kwargs):
        try:
            if not workspace_id:
                workspace_id = uuid.uuid1()
            _workdir = os.path.join(jinad_args.workspace, str(workspace_id))
            Path(_workdir).mkdir(parents=True, exist_ok=True)

            y_spec = config.read().decode()
            f = Flow.load_config(y_spec)

            with change_cwd(_workdir):
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
                'workdir': _workdir
            }
            return _id
