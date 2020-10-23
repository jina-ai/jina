__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np
from typing import Dict, Any
from jina.executors.decorators import batching, as_ndarray
from jina.executors.encoders.multimodal import BaseMultiModalEncoder


class ConcatenateMultiModalEncoder(BaseMultiModalEncoder):
    def __init__(self,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

    @batching
    @as_ndarray
    def encode(self, data: Dict[str, Any], *args, **kwargs):
        return np.concatenate((data['modality1'], data['modality2']), axis=1)
