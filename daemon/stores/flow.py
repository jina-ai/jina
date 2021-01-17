import uuid
from tempfile import SpooledTemporaryFile
from typing import Optional, List

from fastapi import UploadFile

from jina.flow import Flow
from .base import BaseStore


class FlowStore(BaseStore):

    def add(self, config: SpooledTemporaryFile,
            dependencies: Optional[List[UploadFile]] = None,
            **kwargs):
        try:
            _workdir = self.get_temp_dir()
            if dependencies:
                self.create_files_from_upload(dependencies, _workdir)
            y_spec = config.read().decode()
            f = Flow.load_config(y_spec).start()
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
