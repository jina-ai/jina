import os
import unittest

import numpy as np

from jina.executors import BaseExecutor
from jina.executors.encoders.transformer import TransformerTextEncoder
from tests import JinaTestCase


class MyTestCase(JinaTestCase):
    @unittest.skip("skip tests depending on pretraining models")
    def test_encoding_results(self):
        encoder = TransformerTextEncoder()
        test_data = np.array(['a', 'b', 'xy'])
        encoded_data = encoder.encode(test_data)
        self.assertEqual(encoded_data.shape[0], 3)
        self.assertIs(type(encoded_data), np.ndarray)

    @unittest.skip("skip tests depending on pretraining models")
    def test_all_encoders(self):
        from transformers import BertModel, BertTokenizer, OpenAIGPTModel, \
            OpenAIGPTTokenizer, GPT2Model, GPT2Tokenizer, \
            XLNetModel, XLNetTokenizer, XLMModel, \
            XLMTokenizer, DistilBertModel, DistilBertTokenizer, RobertaModel, \
            RobertaTokenizer, XLMRobertaModel, XLMRobertaTokenizer

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

        for model_name in MODELS:
            encoder = TransformerTextEncoder(model_name, max_length=6)
            test_data = np.array(['a', 'b', 'xy'])
            encoded_data = encoder.encode(test_data)
            self.assertEqual(encoded_data.shape[0], 3, '{} failed'.format(model_name))

    def test_save_and_load(self):
        encoder = TransformerTextEncoder(
            max_length=10, pooling_strategy='cls', workspace=os.environ['TEST_WORKDIR'])
        encoder.save_config()
        self.assertTrue(os.path.exists(encoder.config_abspath))

        encoder.touch()
        encoder.save()
        self.assertTrue(os.path.exists(encoder.save_abspath))
        encoder_loaded = BaseExecutor.load(encoder.save_abspath)

        self.assertEqual(encoder_loaded.max_length, encoder.max_length)
        self.assertEqual(encoder_loaded.pooling_strategy, encoder.pooling_strategy)

        self.tmp_files.append(encoder.config_abspath)
        self.tmp_files.append(encoder.save_abspath)
        self.tmp_files.append(encoder_loaded.config_abspath)
        self.tmp_files.append(encoder_loaded.save_abspath)
        self.tmp_files.append(encoder.encoder_abspath)

    def test_save_and_load_config(self):
        encoder = TransformerTextEncoder(max_length=10, pooling_strategy='cls')
        encoder.save_config()
        self.assertTrue(os.path.exists(encoder.config_abspath))

        encoder_loaded = BaseExecutor.load_config(encoder.config_abspath)
        self.assertEqual(encoder_loaded.max_length, encoder.max_length)
        self.assertEqual(encoder_loaded.pooling_strategy, encoder.pooling_strategy)

        self.tmp_files.append(encoder_loaded.config_abspath)
        self.tmp_files.append(encoder_loaded.save_abspath)


if __name__ == '__main__':
    unittest.main()
