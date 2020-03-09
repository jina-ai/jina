import numpy as np
import torch

from . import BaseTextEncoder
from ...excepts import EncoderFailToLoad

from transformers import BertModel, BertTokenizer, OpenAIGPTModel, \
    OpenAIGPTTokenizer, GPT2Model, GPT2Tokenizer, TransfoXLModel, \
    TransfoXLTokenizer, XLNetModel, XLNetTokenizer, XLMModel, \
    XLMTokenizer, DistilBertModel, DistilBertTokenizer, RobertaModel, \
    RobertaTokenizer, XLMRobertaModel, XLMRobertaTokenizer

MODELS = {
    'bert-base-uncased': (BertModel, BertTokenizer),
    'openai-gpt': (OpenAIGPTModel, OpenAIGPTTokenizer),
    'gpt2': (GPT2Model, GPT2Tokenizer),
    # 'transfo-xl-wt103': (TransfoXLModel, TransfoXLTokenizer),
    'xlnet-base-cased': (XLNetModel, XLNetTokenizer),
    'xlm-mlm-enfr-1024': (XLMModel, XLMTokenizer),
    'distilbert-base-cased': (DistilBertModel, DistilBertTokenizer),
    'roberta-base': (RobertaModel, RobertaTokenizer),
    'xlm-roberta-base': (XLMRobertaModel, XLMRobertaTokenizer)
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

    def post_init(self):
        model_class, tokenizer_class = MODELS[self.model_name]

        try:
            self.model = model_class.from_pretrained(self.model_name)
        except Exception:
            self.logger.warning('failed load model')
            raise EncoderFailToLoad

        try:
            self.tokenizer = tokenizer_class.from_pretrained(self.model_name)
        except Exception:
            self.logger.warning('failed load tokenizer')
            raise EncoderFailToLoad

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: a 1d array of string type in size `B`
        :return: an ndarray in size `B x D`
        """
        pad_token_id = self.tokenizer.pad_token_id
        if pad_token_id is None:
            self.tokenizer.pad_token = '<PAD>'
            self.model.resize_token_embeddings(len(self.tokenizer))
        seq_ids = torch.tensor(
            [self.tokenizer.encode(t, max_length=self.max_length, pad_to_max_length=True, padding_side='right')
             for t in data.tolist()])
        mask_ids = torch.tensor(
            [[1] * (len(t) + 2) + [0] * (self.max_length - len(t) - 2) for t in data.tolist()])
        print("{}".format(seq_ids))
        with torch.no_grad():
            seq_output, *extra_output = self.model(seq_ids, attention_mask=mask_ids)
            if self.pooling_strategy == 'cls':
                if len(extra_output) == 1 and isinstance(extra_output[0], torch.Tensor):
                    output = extra_output[0].numpy()
                else:
                    raise NotImplementedError
            else:
                seq_output = seq_output.numpy()
                emb_dim = seq_output.shape[2]
                mask_2d = mask_ids.numpy()
                mask = np.tile(mask_2d, (emb_dim, 1, 1))
                mask = np.rollaxis(mask, 0, 3)
                output = mask * seq_output
                if self.pooling_strategy == 'reduce-mean':
                    output = np.sum(output, axis=1) / np.sum(mask, axis=1)
                elif self.pooling_strategy == 'reduce-max':
                    neg_mask = (mask_2d - 1) * 1e10
                    neg_mask = np.tile(neg_mask, (emb_dim, 1, 1))
                    neg_mask = np.rollaxis(neg_mask, 0, 3)
                    output += neg_mask
                    output = np.max(output, axis=1)
                else:
                    raise NotImplementedError
        return output
