import numpy as np
import pickle
from jina.hub.encoders.numeric import TransformEncoder
from jina.hub.encoders.numeric.pca import IncrementalPCAEncoder
from tests.unit.executors.encoders.numeric import NumericTestCase


class IncrementalPCATestCaseTrainTestCase(NumericTestCase):
    def _get_encoder(self):
        self.requires_train_after_load = True
        self.input_dim = 28
        self.target_output_dim = 7
        encoder = IncrementalPCAEncoder(
            output_dim=self.target_output_dim, whiten=True, num_features=self.input_dim)
        self.train_data = np.random.rand(1000, self.input_dim)
        encoder.train(self.train_data)
        return encoder


class IncrementalPCATestCaseLoadTestCase(NumericTestCase):
    def _get_encoder(self):
        self.requires_train_after_load = False
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = IncrementalPCAEncoder(
            output_dim=self.target_output_dim, whiten=True, num_features=self.input_dim)
        self.train_data = np.random.rand(1000, self.input_dim)
        encoder.train(self.train_data)
        filename = 'pca_model.model'
        pickle.dump(encoder.model, open(filename, 'wb'))
        self.add_tmpfile(filename)
        return TransformEncoder(model_path=filename)
