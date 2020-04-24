__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from . import BaseNumericEncoder
from ..decorators import batching, as_ndarray


class PaddlehubEncoder(BaseNumericEncoder):
    def __init__(self,
                 model_name: str,
                 output_feature: str,
                 pool_strategy: str = None,
                 channel_axis: int = -3,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.pool_strategy = pool_strategy
        self.outputs_name = output_feature
        self.inputs_name = None
        self.channel_axis = channel_axis
        self._default_channel_axis = -3

    def post_init(self):
        import paddlehub as hub
        import paddle.fluid as fluid
        module = hub.Module(name=self.model_name)
        inputs, outputs, self.model = module.context(trainable=False)
        self.get_inputs_and_outputs_name(inputs, outputs)
        place = fluid.CUDAPlace(0) if self.on_gpu else fluid.CPUPlace()
        self.exe = fluid.Executor(place)

    def get_inputs_and_outputs_name(self, input_dict, output_dict):
        raise NotImplementedError

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

    def get_pooling(self, data: 'np.ndarray', axis=None) -> 'np.ndarray':
        _reduce_axis = tuple((i for i in range(len(data.shape)) if i > 1))
        return getattr(np, self.pool_strategy)(data, axis=_reduce_axis)

    def close(self):
        self.exe.close()
