__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Any

import numpy as np

from . import BaseEncoder
from ..clients import BaseTFServingClientExecutor


class BaseTFServingClientEncoder(BaseTFServingClientExecutor, BaseEncoder):
    """
    :class:`BaseTFServingEncoder` is the base class for the encoders that wrap up a tf serving client. The client call
        the gRPC port of the tf server.

    """

    def encode(self, data: Any, *args, **kwargs) -> Any:
        _req = self.get_request(data)
        return self.get_response(_req)


class UnaryTFServingClientEncoder(BaseTFServingClientEncoder):
    """
    :class:`UnaryTFServingEncoder` is an encoder that wraps up a tf serving client. This client covers the simplest
        case, in which both the request and the response have a single data field.

    """

    def __init__(self, input_name: str, output_name: str, *args, **kwargs):
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
