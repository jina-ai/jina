from typing import Any
from ..clients import TFServingClientExecutor
from . import BaseEncoder
import numpy as np


class TFServingEncoder(TFServingClientExecutor, BaseEncoder):
    def encode(self, data: Any, *args, **kwargs) -> Any:
        req = self.prepare_request(data)
        # send requests in an asynchronized way
        resp = self.send_request(req)
        # send requests in an asynchronized way
        self.postprocess_resp(resp)
        return np.random.rand(10, 30)
