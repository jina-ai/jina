from typing import Union, Tuple, List

import numpy as np

from . import BaseTextEncoder


class FlairTextEncoder(BaseTextEncoder):
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
        self.model = None

    def post_init(self):
        from flair.embeddings import WordEmbeddings, FlairEmbeddings, BytePairEmbeddings, PooledFlairEmbeddings, \
            DocumentPoolEmbeddings

        if self.model is not None:
            return
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
            self.logger.info('initialize flair encoder with embeddings: {}'.format(self.embeddings))

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: a 1d array of string type in size `B`
        :return: an ndarray in size `B x D`
        """
        import torch
        from flair.embeddings import Sentence
        c_batch = [Sentence(row) for row in data]
        self.model.embed(c_batch)
        return torch.stack([c_text.get_embedding() for c_text in c_batch]).detach().numpy()
