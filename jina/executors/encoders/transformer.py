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


class PyTorchTransformers(BaseTextEncoder):
    def __init__(self,
                 model_name: str = 'bert-base-uncased',
                 pooling_strategy: str = 'reduce-mean',
                 max_length: int = 64,
                 *args, **kwargs):
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
        pad_token_id = self.tokenizer.pad_token_id
        if pad_token_id is None:
            self.tokenizer.pad_token = '[PAD]'
        seq_ids = torch.tensor(
            [self.tokenizer.encode(t, max_length=self.max_length, pad_to_max_length=True) for t in data.tolist()])
        mask_ids = torch.tensor(
            [[1] * (len(t) + 2) + [0] * (self.max_length - len(t) - 2) for t in data.tolist()])
        with torch.no_grad():
            seq_output, *extra_output = self.model(seq_ids, attention_mask=mask_ids)
            if len(extra_output) == 1 and isinstance(extra_output[0], torch.Tensor):
                output = extra_output[0].numpy()
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
