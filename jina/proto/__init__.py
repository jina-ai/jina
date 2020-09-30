__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

"""
The :mod:`jina.proto` defines the protobuf used in jina. It is the core message protocol used in communicating between :class:`jina.peapods.base.BasePod`. It also defines the interface of a gRPC service.
"""

from typing import List, Optional

from google.protobuf.field_mask_pb2 import FieldMask

import jina.proto.jina_pb2
from .jina_pb2 import Request


def is_data_request(req: 'Request') -> bool:
    """check if the request is data request

    DRY_RUN is a ControlRequest but considered as data request
    """
    req_type = type(req)
    return req_type != Request.ControlRequest


class HashProto:
    def __init__(self, paths: List[str] = None, proto_type: str = 'Document'):
        """ A class that generates SIPHash for a protobuf object

        :param paths: protobuf FieldMask paths https://developers.google.com/protocol-buffers/docs/reference/csharp/class/google/protobuf/well-known-types/field-mask
        :param proto_type: the type of the protobuf object
        """
        self._fm = None  # type: Optional['FieldMask']
        if paths:
            self._fm = FieldMask(paths=paths)
        self._cls = getattr(jina.proto.jina_pb2, proto_type)

    def __call__(self, proto, context_hash: bytes = b'', salt: bytes = b'', *args, **kwargs) -> str:
        """
        Get hexdigest of a proto object

        :param proto: the protobuf object to hash
        :param context_hash: the binary hash digest of the context, e.g. parent doc
        :param salt: other info that should be taken into consideration when hashing
        :param args:
        :param kwargs:
        :return:
        """
        p = proto
        if self._fm:
            p = self._cls()
            self._fm.MergeMessage(proto, p)
        return hash(p.SerializeToString() + context_hash + salt).to_bytes(8, 'big', signed=True).hex()
