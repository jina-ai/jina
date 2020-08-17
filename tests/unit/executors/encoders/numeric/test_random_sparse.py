import numpy as np
import pickle

from jina.executors.encoders.numeric import FitTransformEncoder
from jina.executors.encoders.numeric.random_sparse import RandomSparseEncoder
from tests.unit.executors.encoders.numeric import NumericTestCase


class RandomSparseEncoderTrainTestCase(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = RandomSparseEncoder(output_dim=self.target_output_dim)
        train_data = np.random.rand(2000, self.input_dim)
        encoder.train(train_data)
        return encoder


class RandomSparseEncoderLoadTestCase(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = RandomSparseEncoder(output_dim=self.target_output_dim)
        train_data = np.random.rand(2000, self.input_dim)
        encoder.train(train_data)
        filename = 'random_sparse_model.model'
        pickle.dump(encoder.model, open(filename, 'wb'))
        self.add_tmpfile(filename)
        return FitTransformEncoder(model_path=filename)
