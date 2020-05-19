from typing import Any
import numpy as np

from ..clients import BaseTFServingClientExecutor
from . import BaseEncoder


class BaseTFServingEncoder(BaseTFServingClientExecutor, BaseEncoder):
    """
    :class:`BaseTFServingEncoder` is the base class for the encoders that wrap up a tf serving client. The client call
        the gRPC port of the tf server.

    To implement your own executor with `tfserving`,

    .. highlight:: python
    .. code-block:: python

        class MyAwesomeTFServingEncoder(BaseTFServingEncoder):
            def get_input(self, data):
                input_1 = data[:, 0]
                input_2 = data[:, 1:]
                return {
                    'my_input_1': inpnut_1.reshape(-1, 1).astype(np.float32),
                    'my_input_2': inpnut_2.astype(np.float32)
                    }

            def get_output(self, response):
                return np.array(response.result().outputs['output_feature'].float_val)

    """
    def encode(self, data: Any, *args, **kwargs) -> Any:
        _req = self.get_request(data)
        _rsp = self._stub.Predict.future(_req, self.timeout)
        output = self.get_response(_rsp)
        return output


class UnaryTFServingEncoder(BaseTFServingEncoder):
    """
    :class:`UnaryTFServingEncoder` is an encoder that wraps up a tf serving client. This client covers the simplest
        case, in which both the request and the response have a single data field.

    """
    def __init__(self, input_name, output_name, *args, **kwargs):
        """
        :param input_name: the name of data field in the request
        :param output_name: the name of data field in the response
        """
        super().__init__(*args, **kwargs)
        self.input_name = input_name
        self.output_name = output_name

    def get_input(self, data):
        return {self.input_name: data.astype(np.float32)}

    def get_output(self, response):
        return np.array(response.result().outputs[self.output_name].float_val)
