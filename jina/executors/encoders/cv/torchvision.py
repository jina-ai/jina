import numpy as np

from .. import BaseImageEncoder


class TorchImageEncoder(BaseImageEncoder):
    """
    :class:`TorchImageEncoder` encodes data from a ndarray, potentially B x (Channel x Height x Width) into a
        ndarray of `B x D`.
    Internally, :class:`TorchImageEncoder` wraps the models from `torchvision.models`.
    https://pytorch.org/docs/stable/torchvision/models.html
    """

    def __init__(self, model_name: str = 'mobilenet_v2', pool_strategy: str = 'mean', *args, **kwargs):
        """

        :param model_name: the name of the model. Supported models include
            ``resnet18``,
            ``alexnet``,
            ``squeezenet1_0``,
            ``vgg16``,
            ``densenet161``,
            ``inception_v3``,
            ``googlenet``,
            ``shufflenet_v2_x1_0``,
            ``mobilenet_v2``,
            ``resnext50_32x4d``,
            ``wide_resnet50_2``,
            ``mnasnet1_0``
        :param pool_strategy: the pooling strategy
            - `None` means that the output of the model will be the 4D tensor output of the last convolutional block.
            - `mean` means that global average pooling will be applied to the output of the last convolutional block, and
                 thus the output of the model will be a 2D tensor.
            - `max` means that global max pooling will be applied.
        """
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.pool_strategy = pool_strategy
        if pool_strategy not in ("mean", "max", None):
            self.logger.error("unknown pool_strategy: {}".format(self.pool_strategy))
            raise NotImplementedError

    def post_init(self):
        import torchvision.models as models
        import torch
        model = getattr(models, self.model_name)(pretrained=True)
        self.model = model.features.eval()
        device = 'cuda:0' if self.on_gpu else 'cpu'
        self.model.to(torch.device(device))

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: a `B x (Channel x Height x Width)` numpy ``ndarray``, `B` is the size of the batch
        :return: a `B x D` numpy ``ndarray``, `D` is the output dimension
        """
        import torch
        feature_map = self.model(torch.from_numpy(data.astype('float32'))).detach().numpy()
        if feature_map.ndim == 2 or self.pool_strategy is None:
            return feature_map
        return getattr(np, self.pool_strategy)(feature_map, axis=(2, 3))
