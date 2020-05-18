from typing import Any
import numpy as np

from ..clients import TFServingClientExecutor
from . import BaseEncoder


class TFServingEncoder(TFServingClientExecutor, BaseEncoder):
    def encode(self, data: Any, *args, **kwargs) -> Any:
        req = self.get_request({self.input_name: data})
        _feature = self._stub.Predict.future(req, self.timeout)
        if _feature.exception():
            self.logger.error('exception raised in encoding: {}'.format(_feature.exception))
            raise ValueError
        return np.array(_feature.result().outputs[self.output_name].float_val)
