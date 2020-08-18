import tempfile
import os

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from tests.unit.executors.encoders.image import ImageTestCase
from jina.hub.encoders.image.torchvision import CustomImageTorchEncoder
from jina.executors import BaseExecutor


class TestNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 10, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(10, 16, 5)
        self.fc1 = nn.Linear(16 * 53 * 53, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.view(-1, 16 * 53 * 53)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x


class CustomTorchTestCase(ImageTestCase):
    def _get_encoder(self, metas):
        path = tempfile.NamedTemporaryFile().name
        self.add_tmpfile(path)
        model = TestNet()
        torch.save(model, path)
        self.target_output_dim = 10
        self.input_dim = 224
        return CustomImageTorchEncoder(model_path=path, layer_name='conv1', metas=metas)

    def test_encoding_results(self):
        encoder = self.get_encoder()
        if encoder is None:
            return
        test_data = np.random.rand(2, 3, self.input_dim, self.input_dim)
        encoded_data = encoder.encode(test_data)
        self.assertEqual(encoded_data.shape, (2, self.target_output_dim))

    def test_save_and_load(self):
        encoder = self.get_encoder()
        if encoder is None:
            return
        test_data = np.random.rand(2, 3, self.input_dim, self.input_dim)
        encoded_data_control = encoder.encode(test_data)
        encoder.touch()
        encoder.save()
        self.assertTrue(os.path.exists(encoder.save_abspath))
        encoder_loaded = BaseExecutor.load(encoder.save_abspath)
        encoded_data_test = encoder_loaded.encode(test_data)
        self.assertEqual(encoder_loaded.channel_axis, encoder.channel_axis)
        np.testing.assert_array_equal(encoded_data_control, encoded_data_test)

    def test_save_and_load_config(self):
        encoder = self.get_encoder()
        if encoder is None:
            return
        encoder.save_config()
        self.assertTrue(os.path.exists(encoder.config_abspath))
        encoder_loaded = BaseExecutor.load_config(encoder.config_abspath)
        self.assertEqual(encoder_loaded.channel_axis, encoder.channel_axis)
