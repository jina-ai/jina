__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from ..frameworks import BaseCVTFEncoder
from ...decorators import batching, as_ndarray


class KerasImageEncoder(BaseCVTFEncoder):
    """
    :class:`KerasImageEncoder` encodes data from a ndarray, potentially B x (Channel x Height x Width) into a
        ndarray of `B x D`.
    Internally, :class:`KerasImageEncoder` wraps the models from `tensorflow.keras.applications`.
    https://keras.io/applications/
    """

    def __init__(self, img_shape: int = 96,
                 pool_strategy: str = 'avg', channel_axis: int = -1, *args, **kwargs):
        """

        :param model_name: the name of the model. Supported models include
            ``DenseNet121``, ``DenseNet169``, ``DenseNet201``,
            ``InceptionResNetV2``,
            ``InceptionV3``,
            ``MobileNet``, ``MobileNetV2``,
            ``NASNetLarge``, ``NASNetMobile``,
            ``ResNet101``, ``ResNet152``, ``ResNet50``, ``ResNet101V2``, ``ResNet152V2``, ``ResNet50V2``,
            ``VGG16``, ``VGG19``,
            ``Xception``,
        :param pool_strategy: the pooling strategy
            - `None` means that the output of the model will be the 4D tensor output of the last convolutional block.
            - `avg` means that global average pooling will be applied to the output of the last convolutional block, and
                 thus the output of the model will be a 2D tensor.
            - `max` means that global max pooling will be applied.
        :param channel_axis: the axis id of the channel, -1 indicate the color channel info at the last axis.
                If given other, then ``np.moveaxis(data, channel_axis, -1)`` is performed before :meth:`encode`.
        """
        super().__init__(*args, **kwargs)
        if self.model_name is None:
            self.model_name = 'MobileNetV2'
        self.pool_strategy = pool_strategy
        self.img_shape = img_shape
        self.channel_axis = channel_axis

    def post_init(self):
        self.to_device()
        import tensorflow as tf
        model = getattr(tf.keras.applications, self.model_name)(
            input_shape=(self.img_shape, self.img_shape, 3),
            include_top=False,
            pooling=self.pool_strategy,
            weights='imagenet')
        model.trainable = False
        self.model = model

    @batching
    @as_ndarray
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: a `B x (Channel x Height x Width)` numpy ``ndarray``, `B` is the size of the batch
        :return: a `B x D` numpy ``ndarray``, `D` is the output dimension
        """
        if self.channel_axis != -1:
            data = np.moveaxis(data, self.channel_axis, -1)
        return self.model(data)
