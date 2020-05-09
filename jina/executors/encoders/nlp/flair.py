__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Union, Tuple, List

import numpy as np

from ..frameworks import BaseTextTorchEncoder
from ...decorators import batching, as_ndarray


class FlairTextEncoder(BaseTextTorchEncoder):
    """
    :class:`FlairTextEncoder` encodes data from an array of string in size `B` into a ndarray in size `B x D`.
    Internally, :class:`FlairTextEncoder` wraps the DocumentPoolEmbeddings from Flair.
    """

    def __init__(self,
                 embeddings: Union[Tuple[str], List[str]] = ('word:glove', 'flair:news-forward', 'flair:news-backward'),
                 pooling_strategy: str = 'mean',
                 *args,
                 **kwargs):
        """

        :param embeddings: the name of the embeddings. Supported models include
        - ``word:[ID]``: the classic word embedding model, the ``[ID]`` are listed at https://github.com/flairNLP/flair/blob/master/resources/docs/embeddings/CLASSIC_WORD_EMBEDDINGS.md
        - ``flair:[ID]``: the contextual embedding model, the ``[ID]`` are listed at https://github.com/flairNLP/flair/blob/master/resources/docs/embeddings/FLAIR_EMBEDDINGS.md
        - ``pooledflair:[ID]``: the pooled version of the contextual embedding model, the ``[ID]`` are listed at https://github.com/flairNLP/flair/blob/master/resources/docs/embeddings/FLAIR_EMBEDDINGS.md
        - ``byte-pair:[ID]``: the subword-level embedding model, the ``[ID]`` are listed at https://github.com/flairNLP/flair/blob/master/resources/docs/embeddings/BYTE_PAIR_EMBEDDINGS.md
        :param pooling_strategy: the strategy to merge the word embeddings into the chunk embedding. Supported
            strategies include ``mean``, ``min``, ``max``.
        """
        super().__init__(*args, **kwargs)
        self.embeddings = embeddings
        self.pooling_strategy = pooling_strategy
        self.max_length = -1  # reserved variable for future usages
        self._post_set_device = False

    def post_init(self):
        import flair
        flair.device = self.device
        from flair.embeddings import WordEmbeddings, FlairEmbeddings, BytePairEmbeddings, PooledFlairEmbeddings, \
            DocumentPoolEmbeddings
        embeddings_list = []
        for e in self.embeddings:
            model_name, model_id = e.split(':', maxsplit=1)
            emb = None
            try:
                if model_name == 'flair':
                    emb = FlairEmbeddings(model_id)
                elif model_name == 'pooledflair':
                    emb = PooledFlairEmbeddings(model_id)
                elif model_name == 'word':
                    emb = WordEmbeddings(model_id)
                elif model_name == 'byte-pair':
                    emb = BytePairEmbeddings(model_id)
            except ValueError:
                self.logger.error('embedding not found: {}'.format(e))
                continue
            if emb is not None:
                embeddings_list.append(emb)
        if embeddings_list:
            self.model = DocumentPoolEmbeddings(embeddings_list, pooling=self.pooling_strategy)
            self.logger.info('flair encoder initialized with embeddings: {}'.format(self.embeddings))
        else:
            self.logger.error('flair encoder initialization failed.')

    @batching
    @as_ndarray
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: a 1d array of string type in size `B`
        :return: an ndarray in size `B x D`
        """
        import torch
        from flair.embeddings import Sentence
        c_batch = [Sentence(row) for row in data]
        self.model.embed(c_batch)
        result = torch.stack([c_text.get_embedding() for c_text in c_batch]).detach()
        if self.on_gpu:
            result = result.cpu()
        return result.numpy()
