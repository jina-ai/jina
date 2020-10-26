__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np
from jina.executors.encoders.multimodal import BaseMultiModalEncoder


class ConcatenateMultiModalEncoder(BaseMultiModalEncoder):

    def __init__(self,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

    def encode(self, *data: 'np.ndarray', **kwargs):
        assert len(data) == 2
        modality1 = data[0]
        modality2 = data[1]
        assert len(modality1) == len(modality2)
        return np.concatenate((modality1, modality2), axis=1)
