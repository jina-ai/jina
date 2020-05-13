__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from ..frameworks import BaseCVTorchEncoder


class ImageTorchEncoder(BaseCVTorchEncoder):
    """
    :class:`ImageTorchEncoder` encodes data from a ndarray, potentially B x (Channel x Height x Width) into a
        ndarray of `B x D`.
    Internally, :class:`ImageTorchEncoder` wraps the models from `torchvision.models`.
    https://pytorch.org/docs/stable/torchvision/models.html
    """

    def __init__(self, pool_strategy: str = 'mean', *args, **kwargs):
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
        if self.model_name is None:
            self.model_name = 'mobilenet_v2'
        if pool_strategy not in ('mean', 'max', None):
            raise NotImplementedError('unknown pool_strategy: {}'.format(self.pool_strategy))
        self.pool_strategy = pool_strategy

    def post_init(self):
        import torchvision.models as models
        if self.pool_strategy is not None:
            self.pool_fn = getattr(np, self.pool_strategy)
        model = getattr(models, self.model_name)(pretrained=True)
        self.model = model.features.eval()
        self.to_device(self.model)

    def _get_features(self, data):
        return self.model(data)

    def _get_pooling(self, feature_map: 'np.ndarray') -> 'np.ndarray':
        if feature_map.ndim == 2 or self.pool_strategy is None:
            return feature_map
        return self.pool_fn(feature_map, axis=(2, 3))
