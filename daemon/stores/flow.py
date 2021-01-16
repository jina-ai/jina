import uuid
from tempfile import SpooledTemporaryFile
from typing import List, Dict, Union

from fastapi import UploadFile

from jina.enums import PodRoleType
from jina.flow import Flow
from .base import BaseStore
from ..helper import create_meta_files_from_upload
from ..models import SinglePodModel, build_pydantic_model


class FlowStore(BaseStore):

    def add(self, config: Union[str, SpooledTemporaryFile, List[SinglePodModel]] = None,
            files: List[UploadFile] = None):
        """ Creates Flow using List[PodModel] or yaml spec """

        # This makes sure `uses` & `py_modules` are created locally in `cwd`
        if isinstance(files, list) and files:
            for f in files:
                create_meta_files_from_upload(f)

        if isinstance(config, str) or isinstance(config, SpooledTemporaryFile):
            y_spec = config.read().decode() if isinstance(config, SpooledTemporaryFile) else config
            flow = Flow.load_config(y_spec)
        elif isinstance(config, list):
            flow = self._new_flow_from_pods(config)
        else:
            raise TypeError(f'{config!r} is not support')

        flow.start()
        _id = uuid.UUID(flow.args.identity)
        self[_id] = {'object': flow, 'files': files}

        return _id

    @staticmethod
    def _new_flow_from_pods(pod_args: List[Dict]):
        """ Since we rely on SinglePodModel, this can accept all params that a Pod can accept """
        flow = Flow()
        for current_pod_args in pod_args:
            # Hacky code here. We build `SinglePodModel` from `Dict` everytime to reset the default values
            SinglePodModel = build_pydantic_model(model_name='SinglePodModel',
                                                  module='pod')
            _current_pod_args = SinglePodModel(**current_pod_args).dict()

            if not _current_pod_args.get('pod_role'):
                _current_pod_args.update(pod_role=PodRoleType.POD)
            _current_pod_args.pop('log_config')
            flow = flow.add(**_current_pod_args)
        return flow
