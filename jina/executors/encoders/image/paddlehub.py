__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from ..paddlehub import PaddlehubEncoder


class ImagePaddlehubEncoder(PaddlehubEncoder):
    """
    :class:`ImagePaddlehubEncoder` encodes data from a ndarray, potentially B x (Channel x Height x Width) into a
        ndarray of `B x D`.
    Internally, :class:`ImagePaddlehubEncoder` wraps the models from `paddlehub`.
    https://github.com/PaddlePaddle/PaddleHub
    """
    def __init__(self,
                 model_name: str = 'xception71_imagenet',
                 *args, **kwargs):
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
        if 'pool_strategy' in kwargs:
            kwargs.pop('pool_strategy')
        if 'output_feature' in kwargs:
            kwargs.pop('output_feature')
        super().__init__(model_name, output_feature=None, pool_strategy='mean', *args, **kwargs)

    def get_inputs_and_outputs_name(self, input_dict, output_dict):
        self.inputs_name = input_dict['image'].name
        self.outputs_name = output_dict['feature_map'].name
        if self.model_name.startswith('vgg') or self.model_name.startswith('alexnet'):
            self.outputs_name = '@HUB_{}@fc_1.tmp_2'.format(self.model_name)

    def close(self):
        self.exe.close()
