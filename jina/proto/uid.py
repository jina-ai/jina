"""

Remarks on the ``id``, we have three views for it

- ``id``: ``str`` is a hex string, for non-binary environment such as HTTP, CLI, HTML and also human-readable. it will be used as the major view.
- ``bytes``: ``bytes`` is the binary format of str, it has 8 bytes fixed length, so it can be used in the dense file storage, e.g. BinaryPbIndexer, as it requires the key has to be fixed length.
- ``hash``:``int64`` is the integer form of bytes, as 8 bytes map to int64 . This is useful when sometimes you want to use key along with other numeric values together in one ndarray, such as ranker and Numpyindexer

"""

__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import sys
from binascii import unhexlify
from hashlib import blake2b

from .jina_pb2 import Document

_doc_field_mask = None
_digest_size = 8


def new_doc_hash(doc: 'Document') -> int:
    return id2hash(new_doc_id(doc))


def new_doc_id(doc: 'Document') -> str:
    """ Generate a new hexdigest based on the content of the document.

    .. note::
        Always use it AFTER you fill in the content of the document

    :param doc: a non-empty document
    :return: the hexdigest based on :meth:`blake2b`
    """
    d = doc
    if _doc_field_mask:
        d = Document()
        _doc_field_mask.MergeMessage(doc, d)
    return blake2b(d.SerializeToString(), digest_size=_digest_size).hexdigest()


def new_doc_bytes(doc: 'Document') -> bytes:
    return id2bytes(new_doc_id(doc))


def hash2bytes(value: int) -> bytes:
    return int(value).to_bytes(_digest_size, sys.byteorder, signed=True)


def bytes2hash(value: bytes) -> int:
    return int.from_bytes(value, sys.byteorder, signed=True)


def id2bytes(value: str) -> bytes:
    return unhexlify(value)


def bytes2id(value: bytes) -> str:
    return value.hex()


def hash2id(value: int) -> str:
    return bytes2id(hash2bytes(value))


def id2hash(value: str) -> int:
    return bytes2hash(id2bytes(value))
