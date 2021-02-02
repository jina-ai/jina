"""
Remarks on the ``id``, we have three views for it
- ``id``: ``str`` is a hex string, for non-binary environment such as HTTP, CLI, HTML and also human-readable. it will be used as the major view.
- ``bytes``: ``bytes`` is the binary format of str, it has 8 bytes fixed length, so it can be used in the dense file storage, e.g. BinaryPbIndexer, as it requires the key has to be fixed length.
- ``int``:``int`` (formerly names ``hash``) is the integer form of bytes. This is useful when sometimes you want to use key along with other numeric values together in one ndarray, such as ranker and Numpyindexer
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
import warnings
from binascii import unhexlify

import numpy as np

from ...excepts import BadDocID
from ...helper import typename

DIGEST_SIZE = 8
_id_regex = re.compile(r'([0-9a-fA-F][0-9a-fA-F])+')


def int2bytes(value: int) -> bytes:
    return int(value).to_bytes(DIGEST_SIZE, sys.byteorder, signed=True)


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
        elif isinstance(seq, str):
            seq = seq
        elif seq is not None:
            raise BadDocID(f'{typename(seq)}: {seq} is not a valid id')

        return str.__new__(cls, seq)

    def __int__(self):
        """The document id in the integer form of bytes, as 8 bytes map to int64.
        This is useful when sometimes you want to use key along with other numeric values together in one ndarray,
        such as ranker and Numpyindexer
        """
        warnings.warn('UniqueId to int conversion is not reliable and deprecated', DeprecationWarning)
        return id2int(self)

    def __bytes__(self):
        """The document id in the binary format of str, it has 8 bytes fixed length,
        so it can be used in the dense file storage, e.g. BinaryPbIndexer,
        as it requires the key has to be fixed length.
        """
        warnings.warn('UniqueId to str conversion is not reliable and deprecated', DeprecationWarning)
        return id2bytes(self)
