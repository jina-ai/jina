import uuid
from typing import Optional, List, BinaryIO

from fastapi import UploadFile
import os
from jina.flow import Flow
from jina.helper import change_cwd
from .base import BaseStore
from .. import jinad_args


class FlowStore(BaseStore):

    def add(self, config: BinaryIO,
            workspace_id: uuid.UUID,
            **kwargs):
        try:
            y_spec = config.read().decode()
            f = Flow.load_config(y_spec)
            _id = uuid.UUID(f.args.identity)
            _workdir = os.path.join(jinad_args.workspace, str(workspace_id))
            with change_cwd(_workdir):
                f.start()
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
