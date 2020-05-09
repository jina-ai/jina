__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from ..frameworks import BaseTextPaddlehubEncoder
from ...decorators import batching, as_ndarray


class TextPaddlehubEncoder(BaseTextPaddlehubEncoder):
    """
    :class:`TextPaddlehubEncoder` encodes data from an array of string in size `B` into a ndarray in size `B x D`.
    Internally, :class:`TextPaddlehubEncoder` wraps the Ernie module from paddlehub.
    https://github.com/PaddlePaddle/PaddleHub
    """

    def __init__(self,
                 max_length: int = 128,
                 *args,
                 **kwargs):
        """

        :param model_name: the name of the model. Supported models include
            ``ernie``, ``ernie_tiny``, ``ernie_v2_eng_base``, ``ernie_v2_eng_large``,
            ``bert_chinese_L-12_H-768_A-12``, ``bert_multi_cased_L-12_H-768_A-12``,
                ``bert_multi_uncased_L-12_H-768_A-12``, ``bert_uncased_L-12_H-768_A-12``,
                ``bert_uncased_L-24_H-1024_A-16``,
            ``chinese-bert-wwm``, ``chinese-bert-wwm-ext``,
            ``chinese-electra-base``, ``chinese-electra-small``,
            ``chinese-roberta-wwm-ext``, ``chinese-roberta-wwm-ext-large``,
            ``rbt3``, ``rbtl3``
        :param max_length: the max length to truncate the tokenized sequences to.

        For models' details refer to
            https://www.paddlepaddle.org.cn/hublist?filter=en_category&value=SemanticModel
        """
        super().__init__(*args, **kwargs)
        if self.model_name is None:
            self.model_name = 'ernie_tiny'
        self.max_length = max_length

    def post_init(self):
        import paddlehub as hub
        self.model = hub.Module(name=self.model_name)
        self.model.MAX_SEQ_LEN = self.max_length

    @batching
    @as_ndarray
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: a 1d array of string type in size `B`
        :return: an ndarray in size `B x D`
        """
        results = []
        _raw_results = self.model.get_embedding(
            texts=np.atleast_2d(data).reshape(-1, 1).tolist(), use_gpu=self.on_gpu, batch_size=data.shape[0])
        for emb in _raw_results:
            _pooled_feature, _seq_feature = emb
            results.append(_pooled_feature)
        return np.array(results)

    def close(self):
        pass
