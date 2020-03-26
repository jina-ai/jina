import os
import unittest

import numpy as np

from jina.executors import BaseExecutor
from jina.executors.encoders.nlp.transformer import TransformerTextEncoder
from tests import JinaTestCase


class MyTestCase(JinaTestCase):

    @unittest.skipUnless(os.getenv('JINA_TEST_PRETRAINED', False), 'skip the pretrained test if not set')
    def test_pytorch_encoding_results(self):
        encoder = TransformerTextEncoder(model_name='bert-base-uncased')
        test_data = np.array(['a', 'b', 'xy'])
        encoded_data = encoder.encode(test_data)
        self.assertEqual(encoded_data.shape[0], 3)
        self.assertIs(type(encoded_data), np.ndarray)

    @unittest.skipUnless(os.getenv('JINA_TEST_PRETRAINED', False), 'skip the pretrained test if not set')
    def test_tf_encoding_results(self):
        encoder = TransformerTextEncoder(model_name='bert-base-uncased', use_tf=True)
        test_data = np.array(['a', 'b', 'xy'])
        encoded_data = encoder.encode(test_data)
        self.assertEqual(encoded_data.shape[0], 3)
        self.assertIs(type(encoded_data), np.ndarray)

    @unittest.skipUnless('JINA_TEST_PRETRAINED' in os.environ, 'skip the pretrained test if not set')
    def test_all_encoders(self):
        from transformers import BertModel, BertTokenizer, OpenAIGPTModel, \
            OpenAIGPTTokenizer, GPT2Model, GPT2Tokenizer, \
            XLNetModel, XLNetTokenizer, XLMModel, \
            XLMTokenizer, DistilBertModel, DistilBertTokenizer, RobertaModel, \
            RobertaTokenizer, XLMRobertaModel, XLMRobertaTokenizer, TFBertModel, \
            TFOpenAIGPTModel, TFGPT2Model, TFXLNetModel, TFXLMModel, TFDistilBertModel, \
            TFRobertaModel, TFXLMRobertaModel

        MODELS = {
            'bert-base-uncased': (TFBertModel, BertModel, BertTokenizer),
            'openai-gpt': (TFOpenAIGPTModel, OpenAIGPTModel, OpenAIGPTTokenizer),
            'gpt2': (TFGPT2Model, GPT2Model, GPT2Tokenizer),
            'xlnet-base-cased': (TFXLNetModel, XLNetModel, XLNetTokenizer),
            'xlm-mlm-enfr-1024': (TFXLMModel, XLMModel, XLMTokenizer),
            'distilbert-base-cased': (TFDistilBertModel, DistilBertModel, DistilBertTokenizer),
            'roberta-base': (TFRobertaModel, RobertaModel, RobertaTokenizer),
            'xlm-roberta-base': (TFXLMRobertaModel, XLMRobertaModel, XLMRobertaTokenizer)
        }

        for model_name in MODELS:
            encoder = TransformerTextEncoder(model_name, max_length=6)
            test_data = np.array(['a', 'b', 'xy'])
            encoded_data = encoder.encode(test_data)
            self.assertEqual(encoded_data.shape[0], 3, '{} failed'.format(model_name))

    @unittest.skipUnless('JINA_TEST_PRETRAINED' in os.environ, 'skip the pretrained test if not set')
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

    @unittest.skipUnless('JINA_TEST_PRETRAINED' in os.environ, 'skip the pretrained test if not set')
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
