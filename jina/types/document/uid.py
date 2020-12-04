"""

Remarks on the ``id``, we have three views for it

- ``id``: ``str`` is a hex string, for non-binary environment such as HTTP, CLI, HTML and also human-readable. it will be used as the major view.
- ``bytes``: ``bytes`` is the binary format of str, it has 8 bytes fixed length, so it can be used in the dense file storage, e.g. BinaryPbIndexer, as it requires the key has to be fixed length.
- ``hash``:``int64`` is the integer form of bytes, as 8 bytes map to int64 . This is useful when sometimes you want to use key along with other numeric values together in one ndarray, such as ranker and Numpyindexer

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

_doc_field_mask = None
_digest_size = 8
_id_regex = re.compile(r'[0-9a-fA-F]{16}')


def new_doc_hash(doc: 'DocumentProto') -> int:
    return id2hash(new_doc_id(doc))


def new_doc_id(doc: 'DocumentProto') -> str:
    """ Generate a new hexdigest based on the content of the document.

    .. note::
        Always use it AFTER you fill in the content of the document

    :param doc: a non-empty document
    :return: the hexdigest based on :meth:`blake2b`
    """
    d = doc
    if _doc_field_mask:
        d = DocumentProto()
        _doc_field_mask.MergeMessage(doc, d)
    return blake2b(d.SerializeToString(), digest_size=_digest_size).hexdigest()


def new_doc_bytes(doc: 'DocumentProto') -> bytes:
    return id2bytes(new_doc_id(doc))


def hash2bytes(value: int) -> bytes:
    return int(value).to_bytes(_digest_size, sys.byteorder, signed=True)


def bytes2hash(value: bytes) -> int:
    return int.from_bytes(value, sys.byteorder, signed=True)


def id2bytes(value: str) -> bytes:
    try:
        return unhexlify(value)
    except:
        is_valid_id(value)


def bytes2id(value: bytes) -> str:
    return value.hex()


def hash2id(value: int) -> str:
    return bytes2id(hash2bytes(value))


def id2hash(value: str) -> int:
    return bytes2hash(id2bytes(value))


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
            seq = hash2id(int(seq))
        elif isinstance(seq, bytes):
            seq = bytes2id(seq)
        elif seq == '':
            pass
        elif isinstance(seq, str) and is_valid_id(seq):
            seq = seq
        elif seq is not None:
            raise BadDocID(f'{typename(seq)}: {seq} is not a valid id')

        return str.__new__(cls, seq)

    def __hash__(self):
        """The document id in the integer form of bytes, as 8 bytes map to int64.
        This is useful when sometimes you want to use key along with other numeric values together in one ndarray,
        such as ranker and Numpyindexer
        """
        return id2hash(self)

    def __bytes__(self):
        """The document id in the binary format of str, it has 8 bytes fixed length,
        so it can be used in the dense file storage, e.g. BinaryPbIndexer,
        as it requires the key has to be fixed length.
        """
        return id2bytes(self)
