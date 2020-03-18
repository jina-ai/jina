import os
import numpy as np

from .. import BaseImageEncoder


class XCeptionPaddleImageEncoder(BaseImageEncoder):
    """
    :class:`XCeptionPaddleImageEncoder` encodes data from a ndarray, potentially B x (Channel x Height x Width) into a
        ndarray of `B x D`.
    Internally, :class:`XCeptionPaddleImageEncoder` wraps the XCeption module from paddlehub.
    https://github.com/PaddlePaddle/PaddleHub
    """
    def __init__(self, model_name='xception71_imagenet', *args, **kwargs):
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
        ``efficientnetb7_imagenet``,
        ``efficientnetb6_imagenet``,
        ``efficientnetb5_imagenet``,
        ``efficientnetb4_imagenet``,
        ``efficientnetb3_imagenet``,
        ``efficientnetb2_imagenet``,
        ``efficientnetb1_imagenet``,
        ``efficientnetb0_imagenet``,
        ``dpn68_imagenet``,
        ``dpn131_imagenet``,
        ``dpn107_imagenet``,
        ``densenet264_imagenet``,
        ``densenet201_imagenet``,
        ``densenet169_imagenet``,
        ``densenet161_imagenet``,
        ``densenet121_imagenet``,
        ``darknet53_imagenet``,
        ``alexnet_imagenet``,
        # ``pnasnet_imagenet``,
        # ``nasnet_imagenet``


        """
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.inputs_name = ''
        self.outputs_name = ''

    def post_init(self):
        import paddlehub as hub
        import paddle.fluid as fluid
        module = hub.Module(name=self.model_name)
        inputs, outputs, self.model = module.context(trainable=False)
        self.inputs_name = inputs['image'].name
        self.outputs_name = outputs['feature_map'].name
        if self.model_name.startswith('vgg'):
            self.outputs_name = '@HUB_vgg11_imagenet@fc_1.tmp_2'
        elif self.model_name.startswith('alexnet'):
            self.outputs_name = '@HUB_alexnet_imagenet@fc_1.tmp_2'
        place = fluid.CUDAPlace(int(os.getenv('FLAGS_selected_gpus', '0'))) if self.on_gpu else fluid.CPUPlace()
        self.exe = fluid.Executor(place)

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: a `B x (Channel x Height x Width)` numpy ``ndarray``, `B` is the size of the batch
        :return: a `B x D` numpy ``ndarray``, `D` is the output dimension
        """
        feature_map, *_ = self.exe.run(
            program=self.model,
            fetch_list=[self.outputs_name],
            feed={self.inputs_name: data.astype('float32')},
            return_numpy=False
        )
        return np.array(feature_map).squeeze()

    def close(self):
        self.exe.close()
