from unittest.case import TestCase
from unittest.mock import patch


import numpy as np

from jina.hub.encoders.nlp.transformer import TransformerTorchEncoder, TransformerTFEncoder



class MockPtModel:
    def __init__(self, base_model_prefix):
        self.base_model_prefix = base_model_prefix

    # Mocks output of models. Embeds each sequence token into integer number: [0, 1, ..., sequence_length -1]
    def __call__(self, input_ids, *args, **kwargs):
        import torch
        batch_size = input_ids.shape[0]
        seq_length = input_ids.shape[1]
        embed_size = 768
        out = torch.rand((batch_size, seq_length, embed_size))
        return None, (out, )

    def to(self, device):
        pass

    def resize_token_embeddings(self, n_embeddings):
        pass


class MockTFModel(MockPtModel):
    def __call__(self, input_ids, *args, **kwargs):
        import tensorflow as tf
        batch_size = input_ids.shape[0]
        seq_length = input_ids.shape[1]
        embed_size = 768
        out = tf.random.uniform(shape=[batch_size, seq_length, embed_size])
        return None, (out, )


class TransformerEncoderWithMockedModelTestCase(TestCase):
    """To skip weights downloading and model initialization part replaces the actual model with dummy version"""
    texts = ["Never gonna run around", "and desert you"]

    def test_encodes_bert_like(self):
        """Tests that for BERT-like models the embedding from first token is used for sequence embedding"""
        from transformers import AutoModelForPreTraining
        for model in ["bert-base-uncased", "google/electra-base-discriminator", "roberta-base"]:
            with patch.object(AutoModelForPreTraining, 'from_pretrained', return_value=MockPtModel(model)):
                encoder = TransformerTorchEncoder(
                    pretrained_model_name_or_path=model,
                    pooling_strategy='auto',
                    metas={})
                encoded_batch = encoder.encode(self.texts)
                assert encoded_batch.shape == (2, 768)

    def test_encodes_lm_like(self):
        """Tests that for GPT-like language models the embedding from first token is used for sequence embedding"""
        from transformers import AutoModelForPreTraining
        for model in ["gpt2", "openai-gpt"]:
            with patch.object(AutoModelForPreTraining, 'from_pretrained', return_value=MockPtModel(model)):
                encoder = TransformerTorchEncoder(
                    pretrained_model_name_or_path=model,
                    pooling_strategy='auto',
                    metas={})
                encoded_batch = encoder.encode(self.texts)
                assert encoded_batch.shape == (2, 768)

    def test_loads_tf_encoder(self):
        """Tests that TF-based model can be loaded"""
        from transformers import TFAutoModelForPreTraining
        model = "bert-base-uncased"
        with patch.object(TFAutoModelForPreTraining, 'from_pretrained', return_value=MockTFModel(model)):
            encoder = TransformerTFEncoder(pretrained_model_name_or_path=model)
            encoded_batch = encoder.encode(self.texts)
            assert encoded_batch.shape == (2, 768)
