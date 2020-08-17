import numpy as np
import pickle
from jina.executors.encoders.numeric import FitTransformEncoder
from jina.executors.encoders.numeric.feature_agglomeration import FeatureAgglomerationEncoder
from tests.unit.executors.encoders.numeric import NumericTestCase


class FeatureAgglomerationEncoderTrainTestCase(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 200
        self.target_output_dim = 7
        encoder = FeatureAgglomerationEncoder(output_dim=self.target_output_dim)
        train_data = np.random.rand(2000, self.input_dim)
        encoder.train(train_data)
        return encoder


class FeatureAgglomerationEncoderLoadTestCase(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = FeatureAgglomerationEncoder(output_dim=self.target_output_dim)
        train_data = np.random.rand(2000, self.input_dim)
        encoder.train(train_data)
        filename = 'feature_agglomeration_model.model'
        pickle.dump(encoder.model, open(filename, 'wb'))
        self.add_tmpfile(filename)
        return FitTransformEncoder(model_path=filename)
