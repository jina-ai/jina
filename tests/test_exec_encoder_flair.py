import unittest
from jina.executors.encoders.flair import FlairTextEncoder
import numpy as np


class MyTestCase(unittest.TestCase):
    model_subname_dict = {
        'word:': ['glove', 'extvec', 'crawl', 'twitter', 'news'],
        'flair': ['multi-forward', 'multi-backward',
                  'multi-forward-fast', 'multi-backward-fast',
                  'news-forward', 'news-backward',
                  'news-forward-fast', 'news-backward-fast',
                  'mix-forward', 'mix-backward'],
        'byte-pair': ['en', 'de', 'fr'],
        'elmo': ['small', 'medium', 'large', 'original', 'pubmed'],
        # 'fasttext': ['/path/to/custom_fasttext_embeddings.bin']
    }
    model_subname_dict['pooledflair'] = model_subname_dict['flair']
    model_list = ["{}:{}".format(model_name, subname) for model_name, v in model_subname_dict.items() for subname in v]
    pooling_list = [
        'reduce-max', 'reduce-min', 'reduce-mean'
    ]

    @unittest.skip("skip tests depending on pretraining models")
    def test_encoding_results(self):
        encoder = FlairTextEncoder()
        test_data = np.array(['it is a good day!', 'the dog sits on the floor.'])
        encoded_data = encoder.encode(test_data)
        self.assertEqual(encoded_data.shape[0], 2)
        self.assertIs(type(encoded_data), np.ndarray)

    @unittest.skip("skip tests depending on pretraining models")
    def test_all_encoders(self):
        for model_name in MyTestCase.model_list:
            for pooling_strategy in MyTestCase.pooling_list:
                encoder = FlairTextEncoder((model_name), pooling_strategy=pooling_strategy)
                test_data = np.array(['it is a good day!', 'the dog sits on the floor.'])
                encoded_data = encoder.encode(test_data)
                self.assertEqual(encoded_data.shape[0], 2, '{} failed'.format(model_name))


if __name__ == '__main__':
    unittest.main()
