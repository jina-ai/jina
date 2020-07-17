import tempfile
import unittest

from jina.executors.encoders.image.customtorchvision import CustomImageTorchEncoder
from tests.unit.executors.encoders.image import ImageTestCase


class MyTestCase(ImageTestCase):
    def _get_encoder(self, metas):
        import torch
        import torch.nn as nn
        import torch.nn.functional as F

        class TestNet(nn.Module):
            def __init__(self):
                super(TestNet, self).__init__()
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

        path = tempfile.NamedTemporaryFile().name
        self.add_tmpfile(path)
        model = TestNet()
        torch.save(model, path)
        self.target_output_dim = 10
        self.input_dim = 224
        return CustomImageTorchEncoder(model_path=path, layer_name='conv1', metas=metas)


if __name__ == '__main__':
    unittest.main()
