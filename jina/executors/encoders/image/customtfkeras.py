__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from .tfkeras import KerasImageEncoder
from ...decorators import batching, as_ndarray



class CustomKerasImageEncoder(KerasImageEncoder):
    """
    :class:`CustomImageKerasEncoder` encodes data from a ndarray, potentially B x (Channel x Height x Width) into a
        ndarray of `B x D`.
    Internally, :class:`CustomImageKerasEncoder` wraps any custom tf.keras model not part of models from `tensorflow.keras.applications`.
    https://www.tensorflow.org/api_docs/python/tf/keras/applications
    """
    
    def __init__(self, model_path: str, layer_name: str, channel_axis: int = -1, *args, **kwargs):

        """
        :param model_path: the path where the model is stored.
        :layer: Name of the layer from where to extract the feature map.
        """
        super().__init__(*args, **kwargs)
        self.model_path = model_path
        self.layer_name = layer_name
        self.channel_axis = channel_axis

    def post_init(self):
        self.to_device()
        import tensorflow as tf
        model = tf.keras.models.load_model(self.model_path)
        model.trainable = False
        self.model = tf.keras.Model(inputs=model.input,
                                    outputs=model.get_layer(self.layer_name).output)
