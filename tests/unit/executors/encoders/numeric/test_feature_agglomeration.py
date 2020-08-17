import numpy as np
import pickle
from jina.executors.encoders.numeric import TransformEncoder
from jina.executors.encoders.numeric.feature_agglomeration import FeatureAgglomerationEncoder
from tests.unit.executors.encoders.numeric import NumericTestCase


class FeatureAgglomerationEncoderTrainTestCase(NumericTestCase):
    def _get_encoder(self):
        self.requires_train_after_load = True
        self.input_dim = 200
        self.target_output_dim = 7
        encoder = FeatureAgglomerationEncoder(output_dim=self.target_output_dim)
        self.train_data = np.random.rand(2000, self.input_dim)
        encoder.train(self.train_data)
        return encoder


class FeatureAgglomerationEncoderLoadTestCase(NumericTestCase):
    def _get_encoder(self):
        self.requires_train_after_load = False
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = FeatureAgglomerationEncoder(output_dim=self.target_output_dim)
        self.train_data = np.random.rand(2000, self.input_dim)
        encoder.train(self.train_data)
        filename = 'feature_agglomeration_model.model'
        pickle.dump(encoder.model, open(filename, 'wb'))
        self.add_tmpfile(filename)
        return TransformEncoder(model_path=filename)
