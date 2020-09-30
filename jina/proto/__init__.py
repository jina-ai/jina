"""
The :mod:`jina.proto` defines the protobuf used in jina. It is the core message protocol used in communicating between :class:`jina.peapods.base.BasePod`. It also defines the interface of a gRPC service.
"""

__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from binascii import unhexlify
from typing import Optional

from .jina_pb2 import Request, Document

doc_field_mask = None  # type: Optional['FieldMask']


def is_data_request(req: 'Request') -> bool:
    """check if the request is data request

    DRY_RUN is a ControlRequest but considered as data request
    """
    req_type = type(req)
    return req_type != Request.ControlRequest


def new_doc_hash(doc: 'Document') -> int:
    d = doc
    if doc_field_mask:
        d = Document()
        doc_field_mask.MergeMessage(doc, d)
    return hash(d.SerializeToString())


def new_doc_id(doc: 'Document') -> str:
    return hash2id(new_doc_hash(doc))


def hash2bytes(value: int) -> bytes:
    return value.to_bytes(8, 'big', signed=True)


def bytes2hash(value: bytes) -> int:
    return int.from_bytes(value, 'big', signed=True)


def id2bytes(value: str) -> bytes:
    return unhexlify(value)


def bytes2id(value: bytes) -> str:
    return value.hex()


def hash2id(value: int) -> str:
    return bytes2id(hash2bytes(value))


def id2hash(value: str) -> int:
    return bytes2hash(id2bytes(value))
