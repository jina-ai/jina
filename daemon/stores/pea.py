import uuid
from argparse import Namespace
from pathlib import Path

from jina.helper import change_cwd
from jina.peapods import Pea
from .base import BaseStore
from .helper import get_workspace_path


class PeaStore(BaseStore):
    peapod_cls = Pea

    def add(self, args: Namespace,
            **kwargs):
        try:
            workspace_id = args.workspace_id
            if not workspace_id:
                workspace_id = uuid.uuid1()

            _workdir = get_workspace_path(workspace_id)
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
                'workdir': _workdir,
                'workspace_id': workspace_id
            }
            return _id
