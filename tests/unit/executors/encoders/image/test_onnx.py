import unittest

from jina.executors.encoders.image.onnx import OnnxImageEncoder
from tests.unit.executors.encoders.image import ImageTestCase


class MyTestCase(ImageTestCase):
    def _get_encoder(self, metas):
        self.target_output_dim = 1280
        self.input_dim = 224
        return OnnxImageEncoder(
            output_feature='mobilenetv20_features_relu1_fwd',
            model_path='/tmp/onnx/mobilenetv2-1.0/mobilenetv2-1.0.onnx',
            metas=metas)


if __name__ == '__main__':
    unittest.main()
