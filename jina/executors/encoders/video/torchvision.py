__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from ..torchvision import TorchEncoder


class VideoTorchEncoder(TorchEncoder):
    """
    :class:`VideoTorchEncoder` encodes data from a ndarray, potentially B x T x (Channel x Height x Width) into an
        ndarray of `B x D`.
    Internally, :class:`VideoTorchEncoder` wraps the models from `torchvision.models`.
    https://pytorch.org/docs/stable/torchvision/models.html
    """
    def __init__(self, model_name: str = 'r3d_18', *args, **kwargs):
        """

        :param model_name: the name of the model. Supported models include ``r3d_18``, ``mc3_18``, ``r2plus1d_18``
        """
        super().__init__(model_name, *args, **kwargs)
        self._default_channel_axis = 2

    def _build_model(self):
        import torchvision.models.video as models
        self.model = getattr(models, self.model_name)(pretrained=True).eval()

    def _get_features(self, x):
        x = self.model.stem(x)
        x = self.model.layer1(x)
        x = self.model.layer2(x)
        x = self.model.layer3(x)
        x = self.model.layer4(x)
        x = self.model.avgpool(x)
        x = x.flatten(1)
        return x
