import tempfile
import unittest

from jina.executors.encoders.image.customtfkeras import CustomKerasImageEncoder
from tests.unit.executors.encoders.image import ImageTestCase


class MyTestCase(ImageTestCase):
    def _get_encoder(self, metas):
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import Conv2D, Activation, Flatten, Dense

        class TestNet():
            def __init__(self):
                self.model = None
                self.input_shape = (224, 224, 3)
                self.conv = Conv2D(32, (3, 3), padding='same', name='conv1', input_shape=self.input_shape)
                self.activation_relu = Activation('relu')
                self.flatten = Flatten()
                self.dense = Dense(10, name='dense')
                self.activation_softmax = Activation('softmax')

            def create_model(self):
                self.model = Sequential()
                self.model.add(self.conv)
                self.model.add(self.activation_relu)
                self.model.add(self.flatten)
                self.model.add(self.dense)
                self.model.add(self.activation_softmax)
                return self.model

        path = tempfile.NamedTemporaryFile().name
        self.add_tmpfile(path)
        model = TestNet().create_model()
        model.save(path)
        self.target_output_dim = 10
        self.input_dim = 224
        return CustomKerasImageEncoder(model_path=path, layer_name='dense')


if __name__ == '__main__':
    unittest.main()
