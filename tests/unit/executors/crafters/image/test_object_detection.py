import os
import pytest
from jina.executors.crafters.image.object_detection import TorchObjectDetectionSegmenter
from tests.unit.executors.crafters.image import JinaImageTestCase


class TorchObjectDetectionTestCase(JinaImageTestCase):
    @pytest.mark.skipif('JINA_TEST_PRETRAINED' not in os.environ, reason='skip the pretrained test if not set')
    def test_encoding_fasterrcnn_results(self):
        img_array = self.create_random_img_array(128, 64)
        shape = img_array.shape
        crafter = TorchObjectDetectionSegmenter(channel_axis=-1)
        chunks = crafter.craft(img_array)
        for chunk in chunks:
            self.assertEqual(chunk['blob'].shape, shape)

    @pytest.mark.skipif('JINA_TEST_PRETRAINED' not in os.environ, reason='skip the pretrained test if not set')
    def test_encoding_maskrcnn_results(self):
        img_array = self.create_random_img_array(128, 64)
        shape = img_array.shape
        crafter = TorchObjectDetectionSegmenter(model_name='maskrcnn_resnet50_fpn', channel_axis=-1)
        chunks = crafter.craft(img_array)
        for chunk in chunks:
            self.assertEqual(chunk['blob'].shape, shape)

