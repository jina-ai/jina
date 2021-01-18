import os
import uuid
from argparse import Namespace
from pathlib import Path
from typing import Optional

from jina.helper import change_cwd
from jina.peapods import Pea
from .base import BaseStore
from .. import jinad_args


class PeaStore(BaseStore):
    peapod_cls = Pea

    def add(self, args: Namespace,
            workspace_id: Optional[uuid.UUID] = None,
            **kwargs):
        try:
            if not workspace_id:
                workspace_id = uuid.uuid1()
            _workdir = os.path.join(jinad_args.workspace, str(workspace_id))
            Path(_workdir).mkdir(parents=True, exist_ok=True)

            with change_cwd(_workdir):
                p = self.peapod_cls(args).start()

            _id = uuid.UUID(args.identity)
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
