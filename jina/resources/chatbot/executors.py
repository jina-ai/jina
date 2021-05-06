from typing import Optional, Dict

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

from jina import Executor, DocumentArray, requests


class TransformerEncoder(Executor):
    """
    Wraps the pytorch version of transformers from huggingface.

    :param pretrained_model_name_or_path: Either:
        - a string, the `model id` of a pretrained model hosted
            inside a model repo on huggingface.co, e.g.: ``bert-base-uncased``.
        - a path to a `directory` containing model weights saved using
            :func:`~transformers.PreTrainedModel.save_pretrained`, e.g.:
            ``./my_model_directory/``.
    :param base_tokenizer_model: The name of the base model to use for creating
        the tokenizer. If None, will be equal to `pretrained_model_name_or_path`.
    :param pooling_strategy: the strategy to merge the word embeddings into the
        chunk embedding. Supported strategies include 'cls', 'mean', 'max', 'min'.
    :param layer_index: index of the transformer layer that is used to create
        encodings. Layer 0 corresponds to the embeddings layer
    :param max_length: the max length to truncate the tokenized sequences to.
    :param acceleration: The method to accelerate encoding. The available options are:
        - ``'amp'``, which uses `automatic mixed precision
            `<https://pytorch.org/docs/stable/amp.html>`_ autocasting.
            This option is only available on GPUs that support it
            (architecture newer than or equal to NVIDIA Volatire).
        - ``'quant'``, which uses dynamic quantization on the transformer model.
            See `this tutorial
            <https://pytorch.org/tutorials/intermediate/dynamic_quantization_bert_tutorial.html>`_
            for more information. This option is currently not supported on GPUs.
    :param embedding_fn_name: name of the function to be called from the `model` to do the embedding. `__call__` by default.
            Other possible values would `embed_questions` for `RetriBert` based models
    :param args:  Additional positional arguments
    :param kwargs: Additional keyword arguments

    ..note::
        While acceleration methods can significantly speed up the encoding,
        they result in loss of precision. Make sure that the tradeoff is
        worthwhile for your use case.
    """

    def __init__(
            self,
            pretrained_model_name_or_path: str = 'sentence-transformers/distilbert-base-nli-stsb-mean-tokens',
            base_tokenizer_model: Optional[str] = None,
            pooling_strategy: str = 'mean',
            layer_index: int = -1,
            max_length: Optional[int] = None,
            acceleration: Optional[str] = None,
            embedding_fn_name: str = '__call__',
            *args,
            **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.pretrained_model_name_or_path = pretrained_model_name_or_path
        self.base_tokenizer_model = (
                base_tokenizer_model or pretrained_model_name_or_path
        )
        self.pooling_strategy = pooling_strategy
        self.layer_index = layer_index
        self.max_length = max_length
        self.acceleration = acceleration
        self.embedding_fn_name = embedding_fn_name
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_tokenizer_model)
        self.model = AutoModel.from_pretrained(
            self.pretrained_model_name_or_path, output_hidden_states=True
        )
        self.to_device(self.model)

    def amp_accelerate(self):
        """Check acceleration method """
        import torch
        from contextlib import nullcontext

        if self.acceleration == 'amp':
            return torch.cuda.amp.autocast()
        else:
            return nullcontext()

    def _compute_embedding(self, hidden_states: 'torch.Tensor', input_tokens: Dict):
        import torch

        fill_vals = {'cls': 0.0, 'mean': 0.0, 'max': -np.inf, 'min': np.inf}
        fill_val = torch.tensor(fill_vals[self.pooling_strategy], device=self.device)

        layer = hidden_states[self.layer_index]
        attn_mask = input_tokens['attention_mask'].unsqueeze(-1).expand_as(layer)
        layer = torch.where(attn_mask.bool(), layer, fill_val)

        embeddings = layer.sum(dim=1) / attn_mask.sum(dim=1)
        return embeddings.cpu().numpy()

    @requests
    def encode(self, docs: 'DocumentArray', *args, **kwargs) -> 'np.ndarray':
        """
        Encode an array of string in size `B` into an ndarray in size `B x D`,
        where `B` is the batch size and `D` is the dimensionality of the encoding.

        :param content: a 1d array of string type in size `B`
        :return: an ndarray in size `B x D` with the embeddings
        """
        import torch

        with torch.no_grad():

            if not self.tokenizer.pad_token:
                self.tokenizer.add_special_tokens({'pad_token': '[PAD]'})
                self.model.resize_token_embeddings(len(self.tokenizer.vocab))

            input_tokens = self.tokenizer(
                docs.extract_fields('content'),
                max_length=self.max_length,
                padding='longest',
                truncation=True,
                return_tensors='pt',
            )
            input_tokens = {k: v.to(self.device) for k, v in input_tokens.items()}

            with self.amp_accelerate():
                outputs = getattr(self.model, self.embedding_fn_name)(
                    **input_tokens
                )
                if isinstance(outputs, torch.Tensor):
                    return outputs.cpu().numpy()
                hidden_states = outputs.hidden_states

            return self._compute_embedding(hidden_states, input_tokens)
