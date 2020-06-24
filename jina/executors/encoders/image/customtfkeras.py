__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from ..frameworks import BaseCVTFEncoder
from ...decorators import batching, as_ndarray



class CustomImageKerasEncoder(BaseCVTFEncoder):
    """
    :class:`CustomImageKerasEncoder` encodes data from a ndarray, potentially B x (Channel x Height x Width) into a
        ndarray of `B x D`.
    Internally, :class:`CustomImageKerasEncoder` wraps any custom tf.keras model not part of models from `tensorflow.keras.applications`.
    https://www.tensorflow.org/api_docs/python/tf/keras/applications
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
        import tensorflow as tf
        model = tf.keras.models.load_model(self.model_path)
        model.trainable = False
        intermediate_layer_model = tf.keras.Model(inputs=model.input,
                                 outputs=model.get_layer(layer_name).output)
        self.model = intermediate_layer_model


    @batching
    @as_ndarray
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """
        :param data: a `B x (Channel x Height x Width)` numpy ``ndarray``, `B` is the size of the batch
        :return: a `B x D` numpy ``ndarray``, `D` is the output dimension
        """
        return self.model(data)
