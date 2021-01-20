import os
import uuid
from pathlib import Path
from typing import List

from fastapi import UploadFile

from jina.helper import random_uuid
from .base import BaseStore
from .helper import get_workspace_path


class WorkspaceStore(BaseStore):

    def add(self, files: List[UploadFile], **kwargs):
        try:
            workspace_id = random_uuid()
            _workdir = get_workspace_path(workspace_id)
            Path(_workdir).mkdir(parents=True, exist_ok=False)
            for f in files:
                dest = os.path.join(_workdir, f.filename)
                with open(dest, 'wb') as fp:
                    content = f.file.read()
                    fp.write(content)
                self._logger.info(f'save uploads to {dest}')
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self[workspace_id] = {
                'arguments': [f.filename for f in files],
                'workdir': _workdir,
                'workspace_id': workspace_id
            }
            return workspace_id
