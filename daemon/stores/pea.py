import os
import uuid
from argparse import Namespace
from typing import Optional, List

from fastapi import UploadFile

from jina.helper import change_cwd
from jina.peapods import Pea
from .base import BaseStore
from .. import jinad_args


class PeaStore(BaseStore):
    peapod_cls = Pea

    def add(self, args: Namespace,
            workspace_id: uuid.UUID,
            **kwargs):
        try:
            _id = uuid.UUID(args.identity)
            _workdir = os.path.join(jinad_args.workspace, str(workspace_id))
            with change_cwd(_workdir):
                p = self.peapod_cls(args).start()
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self[_id] = {
                'object': p,
                'arguments': vars(args),
                'workdir': _workdir
            }
            return _id
