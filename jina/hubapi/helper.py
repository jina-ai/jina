__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import base64

from pkg_resources import resource_stream

from .. import __binary_delimiter__
from ..helper import yaml


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


def get_default_login():
    with resource_stream('jina', '/'.join(('resources', 'hub-builder', 'login.yml'))) as fp:
        login_info = yaml.load(fp)
        for k, v in login_info.items():
            login_info[k] = _decode(v)

    return login_info
