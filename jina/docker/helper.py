__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import base64
import time
from pathlib import Path
from typing import Dict, Union, List

from .. import __binary_delimiter__
from ..logging import JinaLogger


def _encode(clear, key=__binary_delimiter__.decode()):
    enc = []
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return base64.urlsafe_b64encode(''.join(enc).encode()).decode()


def _decode(enc, key=__binary_delimiter__.decode()):
    dec = []
    enc = base64.urlsafe_b64decode(enc).decode()
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return ''.join(dec)


def handle_dot_in_keys(document: Dict[str, Union[Dict, List]]) -> Union[Dict, List]:
    updated_document = {}
    for key, value in document.items():
        if isinstance(value, dict):
            value = handle_dot_in_keys(value)
        if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
            value[0] = handle_dot_in_keys(value[0])
        updated_document[key.replace('.', '_')] = value
    return updated_document


def credentials_file():
    Path.home().joinpath('.jina').mkdir(parents=True, exist_ok=True)
    return Path.home().joinpath('.jina').joinpath('access.yml')
