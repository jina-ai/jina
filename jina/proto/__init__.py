"""
The :mod:`jina.proto` defines the protobuf used in jina. It is the core message protocol used in communicating between :class:`jina.peapods.base.BasePod`. It also defines the interface of a gRPC service.

"""

__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from .jina_pb2 import Request


def is_data_request(req: 'Request') -> bool:
    """check if the request is data request

    DRY_RUN is a ControlRequest but considered as data request
    """
    req_type = type(req)
    return req_type != Request.ControlRequest
