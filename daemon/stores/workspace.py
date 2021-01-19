import os
import uuid
from pathlib import Path
from typing import List

from fastapi import UploadFile

from .base import BaseStore
from .. import jinad_args


class WorkspaceStore(BaseStore):

    def add(self, files: List[UploadFile], **kwargs):
        try:
            _id = uuid.uuid1()
            _workdir = os.path.join(jinad_args.workspace, str(_id))
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
            self[_id] = {
                'arguments': [f.filename for f in files],
                'workdir': _workdir
            }
            return _id
