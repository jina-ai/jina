__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from .torchvision import ImageTorchEncoder


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
