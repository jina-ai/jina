from typing import Union, Tuple, List
import numpy as np
import torch

from flair.embeddings import WordEmbeddings, FlairEmbeddings, BytePairEmbeddings, ELMoEmbeddings, \
    FastTextEmbeddings, PooledFlairEmbeddings
from flair.embeddings import DocumentPoolEmbeddings, Sentence

from . import BaseTextEncoder


class FlairTextEncoder(BaseTextEncoder):
    def __init__(self,
                 embeddings: Union[Tuple[str], List[str]] = ['word:glove', 'flair:news-forward', 'flair:news-backword'],
                 pooling_strategy: str = 'reduce-mean',
                 max_length: int = 64,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        embeddings_list = []
        for e in embeddings:
            sub_name = e[(e.find(':')+1):]
            emb = None
            try:
                if e.startswith('flair:'):
                    emb = FlairEmbeddings(sub_name)
                elif e.startswith('word:'):
                    emb = WordEmbeddings(sub_name)
                elif e.startswith('byte-pair:'):
                    emb = BytePairEmbeddings(sub_name)
                elif e.startswith('elmo:'):   # depends on AllenNLP
                    emb = ELMoEmbeddings(sub_name)
                elif e.startswith('fasttext:'):  # load one's own pretrained model
                    emb = FastTextEmbeddings(sub_name)
                elif e.startswith('pooledflair:'):
                    emb = PooledFlairEmbeddings(sub_name)
            except ValueError:
                self.logger.critical("embedding not found: {}".format(e))
                continue
            if emb is not None:
                embeddings_list.append(emb)
        self.pooling_strategy = None
        self.model = None
        if pooling_strategy == "reduce-mean":
            self.pooling_strategy = 'mean'
        elif pooling_strategy == "reduce-max":
            self.pooling_strategy = 'max'
        elif pooling_strategy == "reduce-min":
            self.pooling_strategy = 'min'
        else:
            self.logger.critical("unknown pooling_strategy: {}".format(pooling_strategy))
            raise NotImplementedError
        if embeddings_list:
            self.model = DocumentPoolEmbeddings(embeddings_list, pooling=self.pooling_strategy)

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        c_batch = []
        for c_idx in range(data.shape[0]):
            c_text = Sentence(data[c_idx])
            c_batch.append(c_text)
        self.model.embed(c_batch)
        return torch.stack([c_text.get_embedding() for c_text in c_batch]).detach().numpy()
