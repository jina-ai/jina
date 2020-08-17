import numpy as np
import pickle

from jina.executors.encoders.numeric import FitTransformEncoder
from jina.executors.encoders.numeric.random_gaussian import RandomGaussianEncoder
from tests.unit.executors.encoders.numeric import NumericTestCase


class RandomGaussianEncoderTrainTestCase(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = RandomGaussianEncoder(output_dim=self.target_output_dim)
        train_data = np.random.rand(2000, self.input_dim)
        encoder.train(train_data)
        return encoder


class RandomGaussianEncoderLoadTestCase(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = RandomGaussianEncoder(output_dim=self.target_output_dim)
        train_data = np.random.rand(2000, self.input_dim)
        encoder.train(train_data)
        filename = 'random_gaussian_model.model'
        pickle.dump(encoder.model, open(filename, 'wb'))
        self.add_tmpfile(filename)
        return FitTransformEncoder(model_path=filename)
