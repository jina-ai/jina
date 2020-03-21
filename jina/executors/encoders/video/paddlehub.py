import numpy as np

from .. import BaseVideoEncoder


class PaddlehubVideoEncoder(BaseVideoEncoder):
    """
    :class:`PaddlehubVideoEncoder` encodes data from a ndarray, potentially B x T x (Channel x Height x Width) into a
        ndarray of `B x D`.
    Internally, :class:`PaddlehubVideoEncoder` wraps the models from `paddlehub`.
    https://github.com/PaddlePaddle/PaddleHub
    """
    def __init__(self,
                 model_name: str = 'tsn_kinetics400',
                 output_feature: str = '@HUB_tsn_kinetics400@reduce_mean_0.tmp_0',
                 pool_strategy: str = None,
                 *args, **kwargs):
        """

        :param model_name: the name of the model. Supported models include ``tsn_kinetics400``, ``stnet_kinetics400``,
            ``tsm_kinetics400``
        :param output_feature: the name of the layer for feature extraction. Please use the following values for the
            supported models:
            ``tsn_kinetics400``: `@HUB_tsn_kinetics400@reduce_mean_0.tmp_0`
            ``stnet_kinetics400``: ``@HUB_stnet_kinetics400@reshape2_6.tmp_0``
            ``tsm_kinetics400``: ``@HUB_tsm_kinetics400@reduce_mean_0.tmp_0``

        :param pool_strategy: the pooling strategy
            - `None` means that the output of the model will be the output feature.
            - `mean` means that global average pooling will be applied to the output feature, and thus the output of the
                model will be a 2D tensor.
            - `max` means that global max pooling will be applied.
        """
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.outputs_name = output_feature
        self.pool_strategy = pool_strategy
        if pool_strategy not in ('mean', 'max', None):
            raise NotImplementedError('unknown pool_strategy: {}'.format(self.pool_strategy))

    def post_init(self):
        import paddlehub as hub
        import paddle.fluid as fluid
        module = hub.Module(name=self.model_name)
        inputs, outputs, self.model = module.context(trainable=False)
        self.inputs_name = inputs[0].name
        place = fluid.CUDAPlace(0) if self.on_gpu else fluid.CPUPlace()
        self.exe = fluid.Executor(place)

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: a `B x T x (Channel x Height x Width)` numpy ``ndarray``, `B` is the size of the batch, `T` is the
            number of frames
        :return: a `B x D` numpy ``ndarray``, `D` is the output dimension
        """
        feature_map, *_ = self.exe.run(
            program=self.model,
            fetch_list=[self.outputs_name],
            feed={self.inputs_name: data.astype('float32')},
            return_numpy=False
        )
        feature_map = np.array(feature_map).squeeze()
        if feature_map.ndim == 2 or self.pool_strategy is None:
            return feature_map
        return getattr(np, self.pool_strategy)(feature_map, axis=(2, 3))

    def close(self):
        self.exe.close()
