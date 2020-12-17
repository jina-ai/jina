"""

Remarks on the ``id``, we have three views for it

- ``id``: ``str`` is a hex string, for non-binary environment such as HTTP, CLI, HTML and also human-readable. it will be used as the major view.
- ``bytes``: ``bytes`` is the binary format of str, it has 8 bytes fixed length, so it can be used in the dense file storage, e.g. BinaryPbIndexer, as it requires the key has to be fixed length.
- ``int``:``int64`` (formerly names ``hash``) is the integer form of bytes, as 8 bytes map to int64 . This is useful when sometimes you want to use key along with other numeric values together in one ndarray, such as ranker and Numpyindexer

.. note:

    Customized ``id`` is acceptable as long as
    - it only contains the symbols "0"–"9" to represent values 0 to 9,
    and "A"–"F" (or alternatively "a"–"f").
    - it has even length.
"""

__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import re
import sys
from binascii import unhexlify
from hashlib import blake2b

import numpy as np

from ...excepts import BadDocID
from ...helper import typename
from ...proto.jina_pb2 import DocumentProto

from jina.logging import default_logger

_digest_size = 8
_id_regex = re.compile(r'[0-9a-fA-F]{16}')
_warned_deprecation = False


def get_content_hash(doc: 'DocumentProto') -> str:
    """ Generate a new hexdigest based on the content of the document.

    :param doc: a non-empty document
    :return: the hexdigest based on :meth:`blake2b`
    """
    # TODO: once `new_doc_id` is removed, the content of this function can directly move to the `Document`.
    doc_without_id = DocumentProto()
    doc_without_id.CopyFrom(doc)
    doc_without_id.id = ""
    return blake2b(doc_without_id.SerializeToString(), digest_size=_digest_size).hexdigest()


def new_doc_id(doc: 'DocumentProto') -> str:
    """ Generate a new hexdigest based on the content of the document.

    .. note::
        Always use it AFTER you fill in the content of the document

    :param doc: a non-empty document
    :return: the hexdigest based on :meth:`blake2b`
    """
    global _warned_deprecation
    if not _warned_deprecation:
        default_logger.warning('This function name is deprecated and will be renamed to `get_content_hash` latest with Jina 1.0.0. Please already use the updated name.')
        _warned_deprecation = True
    return get_content_hash(doc)


def int2bytes(value: int) -> bytes:
    return int(value).to_bytes(_digest_size, sys.byteorder, signed=True)


def bytes2int(value: bytes) -> int:
    return int.from_bytes(value, sys.byteorder, signed=True)


def id2bytes(value: str) -> bytes:
    try:
        return unhexlify(value)
    except:
        is_valid_id(value)


def bytes2id(value: bytes) -> str:
    return value.hex()


def int2id(value: int) -> str:
    return bytes2id(int2bytes(value))


def id2hash(value: str) -> int:
    return bytes2int(id2bytes(value))


def id2int(value: str) -> int:
    return bytes2int(id2bytes(value))


def is_valid_id(value: str) -> bool:
    if not isinstance(value, str) or not _id_regex.match(value):
        raise BadDocID(f'{value} is not a valid id. Customized ``id`` is only acceptable when: \
        - it only contains chars "0"–"9" to represent values 0 to 9, \
        and "A"–"F" (or alternatively "a"–"f"). \
        - it has 16 chars described above.')
    return True


class UniqueId(str):
    def __new__(cls, seq):
        if isinstance(seq, (int, np.integer)):
            seq = int2id(int(seq))
        elif isinstance(seq, bytes):
            seq = bytes2id(seq)
        elif seq == '':
            pass
        elif isinstance(seq, str) and is_valid_id(seq):
            seq = seq
        elif seq is not None:
            raise BadDocID(f'{typename(seq)}: {seq} is not a valid id')

        return str.__new__(cls, seq)

    def __int__(self):
        """The document id in the integer form of bytes, as 8 bytes map to int64.
        This is useful when sometimes you want to use key along with other numeric values together in one ndarray,
        such as ranker and Numpyindexer
        """
        return id2int(self)

    def __hash__(self):
        """The document id in the integer form of bytes, as 8 bytes map to int64.
        This is useful when sometimes you want to use key along with other numeric values together in one ndarray,
        such as ranker and Numpyindexer
        """
        # Deprecated. Please use `int(doc_id)` instead.
        return id2int(self)

    def __bytes__(self):
        """The document id in the binary format of str, it has 8 bytes fixed length,
        so it can be used in the dense file storage, e.g. BinaryPbIndexer,
        as it requires the key has to be fixed length.
        """
        return id2bytes(self)
