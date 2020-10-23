__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict, Any
from jina.executors.decorators import batching, as_ndarray
from jina.executors.encoders.multimodal import BaseMultiModalEncoder


class ConcatenateMultiModalEncoder(BaseMultiModalEncoder):
    def __init__(self,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: learn how to pass dict as argument
        self.field_by_modality = {'modality1': 'embedding',
                                  'modality2': 'embedding'}

    @batching
    @as_ndarray
    def encode(self, data: Dict[str, Any], *args, **kwargs):
        print(f' MULTIMODAL encoder ENCODE {data}')
