import numpy as np

from .. import BaseVideoEncoder


class TorchVideoEncoder(BaseVideoEncoder):
    """
    :class:`TorchVideoEncoder` encodes data from a ndarray, potentially B x T x (Channel x Height x Width) into an
        ndarray of `B x D`.
    Internally, :class:`TorchVideoEncoder` wraps the models from `torchvision.models`.
    https://pytorch.org/docs/stable/torchvision/models.html
    """
    def __init__(self,
                 model_name: str = 'r3d_18',
                 *args, **kwargs):
        """

        :param model_name: the name of the model. Supported models include ``r3d_18``, ``mc3_18``, ``r2plus1d_18``
        """
        super().__init__(*args, **kwargs)
        self.model_name = model_name

    def post_init(self):
        import torchvision.models.video as models
        import torch
        model = getattr(models, self.model_name)(pretrained=True)
        self.model = model.eval()
        device = 'cuda:0' if self.on_gpu else 'cpu'
        self.model.to(torch.device(device))

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: a `B x T x (Channel x Height x Width)` numpy ``ndarray``, `B` is the size of the batch
        :return: a `B x D` numpy ``ndarray``, `D` is the output dimension
        """
        import torch
        return self._get_features(
            torch.from_numpy(np.moveaxis(data.astype('float32'), 1, 2))).detach().numpy()

    def _get_features(self, x):
        x = self.model.stem(x)
        x = self.model.layer1(x)
        x = self.model.layer2(x)
        x = self.model.layer3(x)
        x = self.model.layer4(x)
        x = self.model.avgpool(x)
        x = x.flatten(1)
        return x
