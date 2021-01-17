import uuid
from argparse import Namespace
from typing import Optional, List

from fastapi import UploadFile

from jina.peapods import Pea
from .base import BaseStore


class PeaStore(BaseStore):
    peapod_cls = Pea

    def add(self, args: Namespace,
            dependencies: Optional[List[UploadFile]] = None,
            **kwargs):
        try:
            _workdir = self.get_temp_dir()
            if dependencies:
                self.create_files_from_upload(dependencies, _workdir)
            _id = uuid.UUID(args.identity)
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
