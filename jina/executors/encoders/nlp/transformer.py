__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os

import numpy as np

from .. import BaseEncoder
from ..frameworks import BaseTextTFEncoder, BaseTextTorchEncoder
from ..helper import reduce_mean, reduce_max, reduce_min, reduce_cls
from ...decorators import batching, as_ndarray


class BaseTransformerEncoder(BaseEncoder):
    """
    :class:`TransformerTextEncoder` encodes data from an array of string in size `B` into an ndarray in size `B x D`.
    """

    def __init__(self,
                 pooling_strategy: str = 'mean',
                 max_length: int = 64,
                 model_path: str = 'transformer',
                 *args, **kwargs):
        """

        :param model_name: the name of the model. Supported models include 'bert-base-uncased', 'openai-gpt', 'gpt2',
            'xlm-mlm-enfr-1024', 'distilbert-base-cased', 'roberta-base', 'xlm-roberta-base', 'flaubert-base-cased',
            'camembert-base', 'ctrl'.
        :param pooling_strategy: the strategy to merge the word embeddings into the chunk embedding. Supported
            strategies include 'cls', 'mean', 'max', 'min'.
        :param max_length: the max length to truncate the tokenized sequences to.
        :param model_path: the path of the encoder model. If a valid path is given, the encoder will be loaded from the
            given path.

        ..warning::
            `model_path` is a relative path in the executor's workspace.
        """
        super().__init__(*args, **kwargs)
        if self.model_name is None:
            self.model_name = 'bert-base-uncased'
        self.pooling_strategy = pooling_strategy
        self.max_length = max_length
        self.raw_model_path = model_path

    @batching
    @as_ndarray
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
        token_ids_batch = self.array2tensor(token_ids_batch)
        mask_ids_batch = self.array2tensor(mask_ids_batch)
        with self.session():
            seq_output, *extra_output = self.model(token_ids_batch, attention_mask=mask_ids_batch)
            _mask_ids_batch = self.tensor2array(mask_ids_batch)
            _seq_output = self.tensor2array(seq_output)
            if self.pooling_strategy == 'cls':
                if hasattr(self._tokenizer, 'cls_token') and len(extra_output) > 0:
                    output = self.tensor2array(extra_output[0])
                else:
                    output = reduce_cls(_seq_output, _mask_ids_batch, self.cls_pos)
            elif self.pooling_strategy == 'mean':
                output = reduce_mean(_seq_output, _mask_ids_batch)
            elif self.pooling_strategy == 'max':
                output = reduce_max(_seq_output, _mask_ids_batch)
            elif self.pooling_strategy == 'min':
                output = reduce_min(_seq_output, _mask_ids_batch)
            else:
                self.logger.error("pooling strategy not found: {}".format(self.pooling_strategy))
                raise NotImplementedError
        return output

    def __getstate__(self):
        if not os.path.exists(self.model_abspath):
            self.logger.info("create folder for saving transformer models: {}".format(self.model_abspath))
            os.mkdir(self.model_abspath)
        self.model.save_pretrained(self.model_abspath)
        self.tokenizer.save_pretrained(self.model_abspath)
        return super().__getstate__()

    def post_init(self):
        self._model = None
        self._tensor_func = None
        self._sess_func = None
        self.tmp_model_path = self.model_abspath if os.path.exists(self.model_abspath) else self.model_name
        self._tokenizer = self.get_tokenizer()
        self.cls_pos = 'tail' if self.model_name == 'xlnet-base-cased' else 'head'

    def array2tensor(self, array):
        return self.tensor_func(array)

    def tensor2array(self, tensor):
        return tensor.numpy()

    @property
    def model_abspath(self) -> str:
        """Get the file path of the encoder model storage

        """
        return self.get_file_from_workspace(self.raw_model_path)

    @property
    def model(self):
        if self._model is None:
            self._model = self.get_model()
        return self._model

    @property
    def session(self):
        if self._sess_func is None:
            self._sess_func = self.get_session()
        return self._sess_func

    @property
    def tensor_func(self):
        if self._tensor_func is None:
            self._tensor_func = self.get_tensor_func()
        return self._tensor_func

    @property
    def tokenizer(self):
        if self._tokenizer is None:
            self._tokenizer = self.get_tokenizer()
        return self._tokenizer

    def get_tokenizer(self):
        from transformers import BertTokenizer, OpenAIGPTTokenizer, GPT2Tokenizer, \
            XLNetTokenizer, XLMTokenizer, DistilBertTokenizer, RobertaTokenizer, XLMRobertaTokenizer, \
            FlaubertTokenizer, CamembertTokenizer, CTRLTokenizer
        tokenizer_dict = {
            'bert-base-uncased': BertTokenizer,
            'openai-gpt': OpenAIGPTTokenizer,
            'gpt2': GPT2Tokenizer,
            'xlnet-base-cased': XLNetTokenizer,
            'xlm-mlm-enfr-1024': XLMTokenizer,
            'distilbert-base-cased': DistilBertTokenizer,
            'roberta-base': RobertaTokenizer,
            'xlm-roberta-base': XLMRobertaTokenizer,
            'flaubert-base-cased': FlaubertTokenizer,
            'camembert-base': CamembertTokenizer,
            'ctrl': CTRLTokenizer
        }
        if self.model_name not in tokenizer_dict:
            self.logger.error('{} not in our supports: {}'.format(self.model_name, ','.join(tokenizer_dict.keys())))
            raise ValueError
        _tokenizer = tokenizer_dict[self.model_name].from_pretrained(self.tmp_model_path)
        _tokenizer.padding_side = 'right'
        if self.model_name in ('openai-gpt', 'gpt2', 'xlm-mlm-enfr-1024', 'xlnet-base-cased'):
            _tokenizer.pad_token = '<PAD>'
        return _tokenizer

    def get_cls_pos(self):
        return 'tail' if self.model_name == 'xlnet-base-cased' else 'head'

    def get_tmp_model_path(self):
        return self.model_abspath if os.path.exists(self.model_abspath) else self.model_name

    def get_model(self):
        raise NotImplementedError

    def get_session(self):
        raise NotImplementedError

    def get_tensor_func(self):
        raise NotImplementedError


class TransformerTFEncoder(BaseTransformerEncoder, BaseTextTFEncoder):
    """
    Internally, TransformerTFEncoder wraps the tensorflow-version of transformers from huggingface.
    """

    def get_model(self):
        from transformers import TFBertModel, TFOpenAIGPTModel, TFGPT2Model, TFXLNetModel, TFXLMModel, \
            TFDistilBertModel, TFRobertaModel, TFXLMRobertaModel, TFCamembertModel, TFCTRLModel
        model_dict = {
            'bert-base-uncased': TFBertModel,
            'openai-gpt': TFOpenAIGPTModel,
            'gpt2': TFGPT2Model,
            'xlnet-base-cased': TFXLNetModel,
            'xlm-mlm-enfr-1024': TFXLMModel,
            'distilbert-base-cased': TFDistilBertModel,
            'roberta-base': TFRobertaModel,
            'xlm-roberta-base': TFXLMRobertaModel,
            'camembert-base': TFCamembertModel,
            'ctrl': TFCTRLModel
        }
        _model = model_dict[self.model_name].from_pretrained(pretrained_model_name_or_path=self.tmp_model_path)
        if self.model_name in ('xlnet-base-cased', 'openai-gpt', 'gpt2', 'xlm-mlm-enfr-1024'):
            _model.resize_token_embeddings(len(self.tokenizer))
        return _model

    def get_session(self):
        import tensorflow as tf
        return tf.GradientTape

    def get_tensor_func(self):
        self.to_device()
        import tensorflow as tf
        return tf.constant


class TransformerTorchEncoder(BaseTransformerEncoder, BaseTextTorchEncoder):
    """
    Internally, TransformerTorchEncoder wraps the pytorch-version of transformers from huggingface.
    """

    def get_model(self):
        from transformers import BertModel, OpenAIGPTModel, GPT2Model, XLNetModel, XLMModel, DistilBertModel, \
            RobertaModel, XLMRobertaModel, FlaubertModel, CamembertModel, CTRLModel
        model_dict = {
            'bert-base-uncased': BertModel,
            'openai-gpt': OpenAIGPTModel,
            'gpt2': GPT2Model,
            'xlnet-base-cased': XLNetModel,
            'xlm-mlm-enfr-1024': XLMModel,
            'distilbert-base-cased': DistilBertModel,
            'roberta-base': RobertaModel,
            'xlm-roberta-base': XLMRobertaModel,
            'flaubert-base-cased': FlaubertModel,
            'camembert-base': CamembertModel,
            'ctrl': CTRLModel
        }
        _model = model_dict[self.model_name].from_pretrained(self.tmp_model_path)
        if self.model_name in ('xlnet-base-cased', 'openai-gpt', 'gpt2', 'xlm-mlm-enfr-1024'):
            _model.resize_token_embeddings(len(self.tokenizer))
        self.to_device(_model)
        return _model

    def get_session(self):
        import torch
        return torch.no_grad

    def get_tensor_func(self):
        import torch
        return torch.tensor

    def array2tensor(self, array):
        tensor = super().array2tensor(array)
        return tensor.cuda() if self.on_gpu else tensor

    def tensor2array(self, tensor):
        return tensor.cpu().numpy() if self.on_gpu else tensor.numpy()
