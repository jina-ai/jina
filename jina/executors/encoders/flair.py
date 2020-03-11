from typing import Union, Tuple, List
import os
import pickle
import numpy as np
import torch

from . import BaseTextEncoder
from ...excepts import BadPersistantFile


class FlairTextEncoder(BaseTextEncoder):
    """
    `FlairTextEncoder` encodes data from an array of string in size `B` into a ndarray in size `B x D`.
    Internally, `FlairTextEncoder` wraps the DocumentPoolEmbeddings from Flair.
    """
    def __init__(self,
                 embeddings: Union[Tuple[str], List[str]] = ('word:glove', 'flair:news-forward', 'flair:news-backward'),
                 pooling_strategy: str = 'reduce-mean',
                 *args,
                 **kwargs):
        """

        :param embeddings: the name of the embeddings. Supported models include
        - 'word:[ID]': the classic word embedding model, the `[ID]` are listed at https://github.com/flairNLP/flair/blob/master/resources/docs/embeddings/CLASSIC_WORD_EMBEDDINGS.md
        - 'flair:[ID]': the contextual embedding model, the `[ID]` are listed at https://github.com/flairNLP/flair/blob/master/resources/docs/embeddings/FLAIR_EMBEDDINGS.md
        = 'pooledflair:[ID]': the pooled version of the contextual embedding model, the `[ID]` are listed at https://github.com/flairNLP/flair/blob/master/resources/docs/embeddings/FLAIR_EMBEDDINGS.md
        - 'byte-pair:[ID]': the subword-level embedding model, the `[ID]` are listed at https://github.com/flairNLP/flair/blob/master/resources/docs/embeddings/BYTE_PAIR_EMBEDDINGS.md
        :param pooling_strategy:
        :param pooling_strategy: the strategy to merge the word embeddings into the chunk embedding. Supported
            strategies include 'reduce-mean', 'reduce-min', 'reduce-max'.
        """
        super().__init__(*args, **kwargs)
        self.embeddings = embeddings
        self.encoder_abspath = ""
        self.pooling_strategy = None
        self.model = None
        if pooling_strategy == "reduce-mean":
            self.pooling_strategy = 'mean'
        elif pooling_strategy == "reduce-max":
            self.pooling_strategy = 'max'
        elif pooling_strategy == "reduce-min":
            self.pooling_strategy = 'min'
        else:
            self.logger.error("unknown pooling_strategy: {}".format(pooling_strategy))
            raise NotImplementedError

    def post_init(self):
        from flair.embeddings import WordEmbeddings, FlairEmbeddings, BytePairEmbeddings, PooledFlairEmbeddings
        # ELMoEmbeddings, FastTextEmbeddings,

        from flair.embeddings import DocumentPoolEmbeddings

        if self.encoder_abspath:
            if not os.path.exists(self.encoder_abspath):
                self.logger.error("encoder path not found: {}".format(self.encoder_abspath))
                raise FileNotFoundError
            try:
                with open(self.encoder_abspath, 'rb') as fp:
                    self.model = pickle.load(fp)
                    self.logger.info('load flair encoder model from {}'.format(self.encoder_abspath))
            except EOFError:
                raise BadPersistantFile('broken file {} can not be loaded'.format(self.encoder_abspath))
        embeddings_list = []
        for e in self.embeddings:
            model_name, model_id = e.split(':', maxsplit=1)
            emb = None
            try:
                if model_name == 'flair':
                    emb = FlairEmbeddings(model_id)
                elif model_name == 'word':
                    emb = WordEmbeddings(model_id)
                elif model_name == 'byte-pair':
                    emb = BytePairEmbeddings(model_id)
                elif model_name == 'pooledflair':
                    emb = PooledFlairEmbeddings(model_id)
            except ValueError:
                self.logger.error("embedding not found: {}".format(e))
                continue
            if emb is not None:
                embeddings_list.append(emb)
        if embeddings_list:
            self.model = DocumentPoolEmbeddings(embeddings_list, pooling=self.pooling_strategy)

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: a 1d array of string type in size `B`
        :return: an ndarray in size `B x D`
        """
        from flair.embeddings import Sentence
        c_batch = []
        for c_idx in range(data.shape[0]):
            c_text = Sentence(data[c_idx])
            c_batch.append(c_text)
        self.model.embed(c_batch)
        return torch.stack([c_text.get_embedding() for c_text in c_batch]).detach().numpy()

    def __getstate__(self):
        save_path = os.path.join(self.current_workspace, "flair")
        self.encoder_abspath = os.path.join(save_path, "model.bin")
        if not os.path.exists(save_path):
            self.logger.info("create folder for saving flair models: {}".format(save_path))
            os.mkdir(save_path)
        with open(self.encoder_abspath, 'wb') as f:
            pickle.dump(self.model, f)
        return super().__getstate__()
