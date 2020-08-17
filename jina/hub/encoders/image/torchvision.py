__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from jina.executors.decorators import batching, as_ndarray
from jina.executors.encoders.frameworks import BaseTorchEncoder


class ImageTorchEncoder(BaseTorchEncoder):
    """
    :class:`ImageTorchEncoder` encodes data from a ndarray, potentially B x (Channel x Height x Width) into a
        ndarray of `B x D`.
    Internally, :class:`ImageTorchEncoder` wraps the models from `torchvision.models`.
    https://pytorch.org/docs/stable/torchvision/models.html
    """

    def __init__(self, model_name: str = None,
                 pool_strategy: str = 'mean',
                 channel_axis: int = 1,
                 *args, **kwargs):
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
        self.channel_axis = channel_axis
        # axis 0 is the batch
        self._default_channel_axis = 1
        self.model_name = 'mobilenet_v2' or model_name
        if pool_strategy not in ('mean', 'max', None):
            raise NotImplementedError(f'unknown pool_strategy: {self.pool_strategy}')
        self.pool_strategy = pool_strategy

    def post_init(self):
        super().post_init()
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

    @batching
    @as_ndarray
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        if self.channel_axis != self._default_channel_axis:
            data = np.moveaxis(data, self.channel_axis, self._default_channel_axis)
        import torch
        _input = torch.from_numpy(data.astype('float32'))
        if self.on_gpu:
            _input = _input.cuda()
        _feature = self._get_features(_input).detach()
        if self.on_gpu:
            _feature = _feature.cpu()
        _feature = _feature.numpy()
        return self._get_pooling(_feature)


class CustomImageTorchEncoder(ImageTorchEncoder):
    """
    :class:`CustomImageTorchEncoder` encodes data from a ndarray, potentially B x (Channel x Height x Width) into a
        ndarray of `B x D`.
    Internally, :class:`CustomImageTorchEncoder` wraps any custom torch model not part of models from `torchvision.models`.
    https://pytorch.org/docs/stable/torchvision/models.html
    """

    def __init__(self, model_path: str, layer_name: str, *args, **kwargs):
        """
        :param model_path: the path where the model is stored.
        :layer: Name of the layer from where to extract the feature map.
        """
        super().__init__(*args, **kwargs)
        self.model_path = model_path
        self.layer_name = layer_name

    def post_init(self):
        import torch
        if self.pool_strategy is not None:
            self.pool_fn = getattr(np, self.pool_strategy)
        self.model = torch.load(self.model_path)
        self.model.eval()
        self.to_device(self.model)
        self.layer = getattr(self.model, self.layer_name)

    def _get_features(self, data):
        feature_map = None

        def get_activation(model, input, output):
            nonlocal feature_map
            feature_map = output.detach()

        handle = self.layer.register_forward_hook(get_activation)
        self.model(data)
        handle.remove()
        return feature_map
