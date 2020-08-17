__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from jina.executors.decorators import batching, as_ndarray
from jina.executors.encoders.frameworks import BasePaddleEncoder


class ImagePaddlehubEncoder(BasePaddleEncoder):
    """
    :class:`ImagePaddlehubEncoder` encodes data from a ndarray, potentially B x (Channel x Height x Width) into a
        ndarray of `B x D`.
    Internally, :class:`ImagePaddlehubEncoder` wraps the models from `paddlehub`.
    https://github.com/PaddlePaddle/PaddleHub
    """

    def __init__(self,
                 model_name: str = None,
                 output_feature: str = None,
                 pool_strategy: str = None,
                 channel_axis: int = -3,
                 *args,
                 **kwargs):
        """

        :param model_name: the name of the model. Supported models include
        ``xception71_imagenet``, ``xception65_imagenet``, ``xception41_imagenet``,
        ``vgg19_imagenet``, ``vgg16_imagenet``, ``vgg13_imagenet``, ``vgg11_imagenet``,
        ``shufflenet_v2_imagenet``,
        ``se_resnext50_32x4d_imagenet``, ``se_resnext101_32x4d_imagenet``,
            ``resnext50_vd_64x4d_imagenet``, ``resnext50_vd_32x4d_imagenet``,
            ``resnext50_64x4d_imagenet``, ``resnext50_32x4d_imagenet``,
            ``resnext152_vd_64x4d_imagenet``, ``resnext152_64x4d_imagenet``, ``resnext152_32x4d_imagenet``,
            ``resnext101_vd_64x4d_imagenet``, ``resnext101_vd_32x4d_imagenet``,
            ``resnext101_64x4d_imagenet``, ``resnext101_32x4d_imagenet``,
            ``resnext101_32x8d_wsl``, ``resnext101_32x48d_wsl``, ``resnext101_32x32d_wsl``, ``resnext101_32x16d_wsl``,
        ``resnet_v2_50_imagenet``, ``resnet_v2_34_imagenet``, ``resnet_v2_18_imagenet``, ``resnet_v2_152_imagenet``,
            ``resnet_v2_101_imagenet``,
        ``mobilenet_v2_imagenet``,
        ``inception_v4_imagenet``,
        ``googlenet_imagenet``,
        ``efficientnetb7_imagenet``, ``efficientnetb6_imagenet``, ``efficientnetb5_imagenet``,
            ``efficientnetb4_imagenet``, ``efficientnetb3_imagenet``, ``efficientnetb2_imagenet``,
            ``efficientnetb1_imagenet``, ``efficientnetb0_imagenet``,
        ``dpn68_imagenet``, ``dpn131_imagenet``, ``dpn107_imagenet``,
        ``densenet264_imagenet``, ``densenet201_imagenet``, ``densenet169_imagenet``, ``densenet161_imagenet``,
            ``densenet121_imagenet``, ``darknet53_imagenet``,
        ``alexnet_imagenet``,

        """
        super().__init__(*args, **kwargs)
        self.pool_strategy = pool_strategy
        self.outputs_name = output_feature
        self.inputs_name = None
        self.channel_axis = channel_axis
        self._default_channel_axis = -3
        self.model_name = model_name
        if self.model_name is None:
            self.model_name = 'xception71_imagenet'
        if self.outputs_name is None:
            self.outputs_name = None
        if self.pool_strategy is None:
            self.pool_strategy = 'mean'

    def post_init(self):
        super().post_init()
        import paddlehub as hub
        module = hub.Module(name=self.model_name)
        inputs, outputs, self.model = module.context(trainable=False)
        self.get_inputs_and_outputs_name(inputs, outputs)
        self.exe = self.to_device()

    def close(self):
        self.exe.close()

    def get_inputs_and_outputs_name(self, input_dict, output_dict):
        self.inputs_name = input_dict['image'].name
        self.outputs_name = output_dict['feature_map'].name
        if self.model_name.startswith('vgg') or self.model_name.startswith('alexnet'):
            self.outputs_name = f'@HUB_{self.model_name}@fc_1.tmp_2'

    @batching
    @as_ndarray
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: a `B x T x (Channel x Height x Width)` numpy ``ndarray``, `B` is the size of the batch, `T` is the
            number of frames
        :return: a `B x D` numpy ``ndarray``, `D` is the output dimension
        """
        if self.channel_axis != self._default_channel_axis:
            data = np.moveaxis(data, self.channel_axis, self._default_channel_axis)
        feature_map, *_ = self.exe.run(
            program=self.model,
            fetch_list=[self.outputs_name],
            feed={self.inputs_name: data.astype('float32')},
            return_numpy=True
        )
        if feature_map.ndim == 2 or self.pool_strategy is None:
            return feature_map
        return self.get_pooling(feature_map)

    def get_pooling(self, data: 'np.ndarray') -> 'np.ndarray':
        _reduce_axis = tuple((i for i in range(len(data.shape)) if i > 1))
        return getattr(np, self.pool_strategy)(data, axis=_reduce_axis)
