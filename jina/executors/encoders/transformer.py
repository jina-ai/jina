import numpy as np
import torch

from . import BaseTextEncoder
from ...excepts import EncoderFailToLoad

from transformers import BertModel, BertTokenizer, OpenAIGPTModel, \
    OpenAIGPTTokenizer, GPT2Model, GPT2Tokenizer, \
    XLNetModel, XLNetTokenizer, XLMModel, \
    XLMTokenizer, DistilBertModel, DistilBertTokenizer, RobertaModel, \
    RobertaTokenizer, XLMRobertaModel, XLMRobertaTokenizer
    # TransfoXLModel, TransfoXLTokenizer, \

MODELS = {
    'bert-base-uncased': (BertModel, BertTokenizer),
    'openai-gpt': (OpenAIGPTModel, OpenAIGPTTokenizer),
    'gpt2': (GPT2Model, GPT2Tokenizer),
    'xlnet-base-cased': (XLNetModel, XLNetTokenizer),
    'xlm-mlm-enfr-1024': (XLMModel, XLMTokenizer),
    'distilbert-base-cased': (DistilBertModel, DistilBertTokenizer),
    'roberta-base': (RobertaModel, RobertaTokenizer),
    'xlm-roberta-base': (XLMRobertaModel, XLMRobertaTokenizer)
    # 'transfo-xl-wt103': (TransfoXLModel, TransfoXLTokenizer),
}


class TransformerTextEncoder(BaseTextEncoder):
    """
    TransformerTextEncoder encodes data from an array of string in size `B` into a ndarray in size `B x D`.
    Internally, TransformerTextEncoder wraps the pytorch-version of transformers from huggingface.
    """
    def __init__(self,
                 model_name: str = 'bert-base-uncased',
                 pooling_strategy: str = 'reduce-mean',
                 max_length: int = 64,
                 *args, **kwargs):
        """

        :param model_name: the name of the model. Supported models include 'bert-base-uncased', 'openai-gpt', 'gpt2',
            'xlm-mlm-enfr-1024', 'distilbert-base-cased', 'roberta-base', 'xlm-roberta-base' .
        :param pooling_strategy: the strategy to merge the word embeddings into the chunk embedding. Supported
            strategies include 'cls', 'reduce-mean', 'reduce-max'.
        :param max_length: the max length to truncate the tokenized sequences to.
        """

        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.pooling_strategy = pooling_strategy
        self.model = None
        self.tokenizer = None
        self.max_length = max_length
        self.cls_pos = None

    def post_init(self):
        model_class, tokenizer_class = MODELS[self.model_name]

        try:
            self.model = model_class.from_pretrained(self.model_name)
        except Exception:
            self.logger.warning('failed load model')
            raise EncoderFailToLoad

        try:
            self.tokenizer = tokenizer_class.from_pretrained(self.model_name)
            self.tokenizer.padding_side = 'right'
        except Exception:
            self.logger.warning('failed load tokenizer')
            raise EncoderFailToLoad

        if self.model_name in ('bert-base-uncased', 'distilbert-base-cased', 'roberta-base', 'xlm-roberta-base'):
            self.cls_pos = 'head'
        elif self.model_name in ('xlnet-base-cased'):
            self.tokenizer.pad_token = '<PAD>'
            self.model.resize_token_embeddings(len(self.tokenizer))
            self.cls_pos = 'tail'
        elif self.model_name in ('openai-gpt', 'gpt2', 'xlm-mlm-enfr-1024'):
            self.tokenizer.pad_token = '<PAD>'
            self.model.resize_token_embeddings(len(self.tokenizer))

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: a 1d array of string type in size `B`
        :return: an ndarray in size `B x D`
        """
        token_ids_batch = []
        mask_ids_batch = []
        for c_idx in range(data.shape[0]):
            token_ids = self.tokenizer.encode(
                data[c_idx], pad_to_max_length=True, max_length=self.max_length)
            mask_ids = [0 if t == self.tokenizer.pad_token_id else 1 for t in token_ids]
            token_ids_batch.append(token_ids)
            mask_ids_batch.append(mask_ids)
        token_ids_batch = torch.tensor(token_ids_batch)
        mask_ids_batch = torch.tensor(mask_ids_batch)
        with torch.no_grad():
            seq_output, *extra_output = self.model(token_ids_batch, attention_mask=mask_ids_batch)
            if self.pooling_strategy == 'cls':
                if self.cls_pos is None:
                    self.logger.critical("cls is not supported: {}".format(self.model_name))
                    raise NotImplementedError
                output = self._reduce_cls(self, seq_output.numpy(), mask_ids_batch.numpy(), cls_pos=self.cls_pos)
            elif self.pooling_strategy == 'reduce-mean':
                output = self._reduce_mean(seq_output.numpy(), mask_ids_batch.numpy())
            elif self.pooling_strategy == 'reduce-max':
                output = self._reduce_max(seq_output.numpy(), mask_ids_batch.numpy())
            else:
                self.logger.critical("pooling strategy not found: {}".format(self.pooling_strategy))
                raise NotImplementedError
        return output

    @staticmethod
    def _reduce_mean(data, mask_2d):
        emb_dim = data.shape[2]
        mask = np.tile(mask_2d, (emb_dim, 1, 1))
        mask = np.rollaxis(mask, 0, 3)
        output = mask * data
        return np.sum(output, axis=1) / np.sum(mask, axis=1)

    @staticmethod
    def _reduce_max(data, mask_2d):
        emb_dim = data.shape[2]
        mask = np.tile(mask_2d, (emb_dim, 1, 1))
        mask = np.rollaxis(mask, 0, 3)
        output = mask * data
        neg_mask = (mask_2d - 1) * 1e10
        neg_mask = np.tile(neg_mask, (emb_dim, 1, 1))
        neg_mask = np.rollaxis(neg_mask, 0, 3)
        output += neg_mask
        return np.max(output, axis=1)

    @staticmethod
    def _reduce_cls(cls, data, mask_2d, cls_pos='head'):
        mask_pruned = cls._prune_mask(mask_2d, cls_pos)
        return cls._reduce_mean(data, mask_pruned)

    @staticmethod
    def _prune_mask(mask, cls_pos='head'):
        result = np.zeros(mask.shape)
        if cls_pos == 'head':
            mask_row = np.zeros((1, mask.shape[1]))
            mask_row[0, 0] = 1
            result = np.tile(mask_row, (mask.shape[0], 1))
        elif cls_pos == 'tail':
            for num_tokens in np.sum(mask, axis=1).tolist():
                result[num_tokens-1] = 1
        else:
            raise NotImplementedError
        return result

