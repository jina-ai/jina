from typing import Any
import numpy as np

from ..clients import TFServingClientExecutor
from . import BaseEncoder


class BaseTFServingEncoder(TFServingClientExecutor, BaseEncoder):
    def encode(self, data: Any, *args, **kwargs) -> Any:
        _req = self.get_request(data)
        _rsp = self._stub.Predict.future(_req, self.timeout)
        output = self.get_response(_rsp)
        return output


class UnaryTFServingEncoder(BaseTFServingEncoder):
    def get_input(self, data):
        return {self.input_name: data.astype(np.float32)}

    def get_output(self, response):
        return np.array(response.result().outputs[self.output_name].float_val)


# class BertTFServingEncoder(TFServingEncoder):
#     def _get_input(self, data):
#         token_id, mask_id, pos_id = tokenizer.tokenize(data)
#         return {
#             'token_id': token_id,
#             'mask_id': mask_id,
#             'pos_id': pos_id
#         }
#
#     def _get_output(self, response):
#         return np.array(response.result().outputs[0].float_val)
