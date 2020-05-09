__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from ..frameworks import BaseTextTorchEncoder
from ...decorators import batching, as_ndarray


class FarmTextEncoder(BaseTextTorchEncoder):
    """FARM-based text encoder: (Framework for Adapting Representation Models)
    https://github.com/deepset-ai/FARM

    It encodes an array of string in size `B` into an ndarray in size `B x D`
    """

    def __init__(self, model_name_or_path: str = 'deepset/bert-base-cased-squad2',
                 num_processes: int = 0, extraction_strategy: str = 'cls_token',
                 extraction_layer: int = -1,
                 *args,
                 **kwargs):
        """

        :param model_name_or_path:  Local directory or public name of the model to load.
        :param num_processes: the number of processes for `multiprocessing.Pool`. Set to value of 0 to disable
                              multiprocessing. Set to None to let Inferencer use all CPU cores. If you want to
                              debug the Language Model, you might need to disable multiprocessing!
        :param extraction_strategy: Strategy to extract vectors. Choices: 'cls_token' (sentence vector), 'reduce_mean'
                               (sentence vector), reduce_max (sentence vector), 'per_token' (individual token vectors)
        :param extraction_layer: number of layer from which the embeddings shall be extracted. Default: -1 (very last layer).
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        if self.model_name is None:
            self.model_name = 'deepset/bert-base-cased-squad2'
        self.num_processes = num_processes
        self.extraction_strategy = extraction_strategy
        self.extraction_layer = extraction_layer

    def post_init(self):
        from farm.infer import Inferencer
        self.model = Inferencer.load(model_name_or_path=self.model_name, task_type='embeddings',
                                     num_processes=self.num_processes)

    @batching
    @as_ndarray
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        basic_texts = [{'text': s} for s in data]
        embeds = np.stack([k['vec'] for k in self.model.extract_vectors(dicts=basic_texts)])
        return embeds
