import numpy as np

from ..frameworks import BaseMindsporeEncoder
from ...decorators import batching, as_ndarray


class CustomMindsporeImageEncoder(BaseMindsporeEncoder):
    def __init__(self, pool_strategy: str = 'mean', channel_axis: int = 1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pool_strategy = pool_strategy
        if pool_strategy not in ('mean', 'max', None):
            raise NotImplementedError(f'unknown pool_strategy: {self.pool_strategy}')

    @batching
    @as_ndarray
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: a `B x (Channel x Height x Width)` numpy ``ndarray``, `B` is the size of the batch
        :return: a `B x D` numpy ``ndarray``, `D` is the output dimension
        """
        from mindspore import Tensor
        if self.channel_axis != 1:
            data = np.moveaxis(data, self.channel_axis, 1)
        return self.model(Tensor(data)).asnumpy()

