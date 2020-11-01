__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from jina.executors.decorators import batching_multi_input, as_ndarray
from jina.executors.encoders.multimodal import BaseMultiModalEncoder


class AllTypesConcatenateMultiModalEncoder(BaseMultiModalEncoder):
    batch_size = 10

    def __init__(self,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

    @batching_multi_input(num_data=4)
    @as_ndarray
    def encode(self, *data: 'np.ndarray', **kwargs):
        assert len(data) == 4
        for d in data:
            assert self.batch_size == AllTypesConcatenateMultiModalEncoder.batch_size
            assert len(d) == self.batch_size
        # modality1 is blob, modality2 is embedding, modality3 is text, modality4 is buffer
        modality1 = data[0]
        modality2 = data[1]
        modality3 = data[2]
        modality4 = data[3]
        assert len(modality1) == len(modality2)
        assert len(modality2) == len(modality4)
        assert len(modality3) == len(modality4)
        assert isinstance(modality3[0], str)
        assert isinstance(modality4[0], bytes)

        embed_modality3 = []
        for _ in modality3:
            embed_modality3.append([3, 3])
        embed_modality3 = np.stack(embed_modality3)

        embed_modality4 = []
        for _ in modality4:
            embed_modality4.append([4, 4])
        embed_modality4 = np.stack(embed_modality4)

        return np.concatenate((modality1, modality2, embed_modality3, embed_modality4), axis=1)
