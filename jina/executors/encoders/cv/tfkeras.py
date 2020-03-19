import numpy as np

from .. import BaseImageEncoder


class KerasImageEncoder(BaseImageEncoder):
    """
    :class:`KerasImageEncoder` encodes data from a ndarray, potentially B x (Channel x Height x Width) into a
        ndarray of `B x D`.
    Internally, :class:`KerasImageEncoder` wraps the models from `tensorflow.keras.applications`.
    https://github.com/PaddlePaddle/PaddleHub
    """

    def __init__(self, model_name: str = 'MobileNetV2', pool_strategy: str = 'avg', *args, **kwargs):
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
        """
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.pool_strategy = pool_strategy

    def post_init(self):
        import tensorflow as tf
        self.model = getattr(tf.keras.applications, self.model_name)(
            input_shape=(224, 224, 3),
            include_top=False,
            pooling=self.pool_strategy,
            weights='imagenet')

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: a `B x (Channel x Height x Width)` numpy ``ndarray``, `B` is the size of the batch
        :return: a `B x D` numpy ``ndarray``, `D` is the output dimension
        """
        return self.model(np.moveaxis(data, 1, -1)).numpy()
