import os
import ssl
from tempfile import NamedTemporaryFile

import aiohttp
import pytest
import requests as req
from docarray import Document, DocumentArray

from jina import Client, Executor, Flow, requests
from jina.helper import random_port
from jina.parsers import set_gateway_parser
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.servers import BaseServer
from jina.serve.runtimes.gateway.request_handling import GatewayRequestHandler


class ExecutorTest(Executor):
    @requests
    def empty(self, docs: DocumentArray, **kwargs):
        print(f"# docs {docs}")


@pytest.fixture
def error_log_level():
    old_env = os.environ.get('JINA_LOG_LEVEL')
    os.environ['JINA_LOG_LEVEL'] = 'ERROR'
    yield
    os.environ['JINA_LOG_LEVEL'] = old_env


def test_tag_update():
    port = random_port()

    f = Flow(port=port, protocol='http').add(uses=ExecutorTest)
    d1 = Document(id='1', prop1='val')
    d2 = Document(id='2', prop2='val')
    with f:
        d1 = {'data': [d1.to_dict()]}
        d2 = {'data': [d2.to_dict()]}
        r1 = req.post(f'http://localhost:{port}/index', json=d1)
        r2 = req.post(f'http://localhost:{port}/index', json=d2)
    assert r1.json()['data'][0]['tags'] == {'prop1': 'val'}
    assert r2.json()['data'][0]['tags'] == {'prop2': 'val'}


@pytest.fixture
def cert_pem():
    """This is the cert entry of a self-signed local cert"""
    # avoid PermissionError on Windows by deleting later
    tmp = NamedTemporaryFile('w', delete=False)
    tmp.write(
        """-----BEGIN CERTIFICATE-----
MIIFazCCA1OgAwIBAgIUE663J9NKJE5sTDXei0ScmKE1TskwDQYJKoZIhvcNAQEL
BQAwRTELMAkGA1UEBhMCQVUxEzARBgNVBAgMClNvbWUtU3RhdGUxITAfBgNVBAoM
GEludGVybmV0IFdpZGdpdHMgUHR5IEx0ZDAeFw0yMTA5MjAwOTQ4NThaFw0yMjA5
MjAwOTQ4NThaMEUxCzAJBgNVBAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEw
HwYDVQQKDBhJbnRlcm5ldCBXaWRnaXRzIFB0eSBMdGQwggIiMA0GCSqGSIb3DQEB
AQUAA4ICDwAwggIKAoICAQC243Axri0Aafq5VsS5+w1QgSIYjhWWCi0frm/w95+O
SleiyQ2nR6Cas2YHViLPo4casch+M5d7fzxzSyezKLoM9FJ7p9rHAc08sjuIkqMt
kDApgfl4Rtco/KqgEr0HELpo6rWG8tby0Wbl82eSm93GUAyZwyuZMdr3Ag6v8ppn
JaUit1oWWs8XZdvEIoRxXQu+APNiKaWWrFjbSXay/ZxbsDrdk7Q+bHLiwYxhx3Bj
SZX9xWPjchFv+fD1pBOyq/P76VGr6B938vEj+EorqUwdiIeW3vgw2FODLg5bXMSo
YR6uZ1V2W8xGwWHpj0s1UChbaOY9thRxvtOrKeW9F4xoFoBrr6ZjkcqD/5mARJz+
Uwee/XhLE7Z5L+eyzLXcXLR2lOs8AXgCmUgAgk0NJi8IPQGZFEBuWVJ7DBO87G7p
DbKMkQ4QGB4dj7lJdHUr6v07Z+Etus7Z+cwjQWe2wdQgDV05E/zCSwWIv4AYbGXs
s1P4XXMeYxxK/74vh7k15TmIiq77A96FaxStK2PZXJjI1dB5DhoC93qCZogq4vup
r6Yk6B29whOlHsBWVL4nW6SYxEDNKyWYRRekiJlcxlw+NpZxBUdC5PwOkh4AZmnW
PpBZv/rCXC7Ow0DS9F9CbfzVynihUHLlZk2SvH8Dc4htum+guiwBMyRtNaSdD8l2
OwIDAQABo1MwUTAdBgNVHQ4EFgQUvTljFuE/DJlq0s8U3wdteIHmQbwwHwYDVR0j
BBgwFoAUvTljFuE/DJlq0s8U3wdteIHmQbwwDwYDVR0TAQH/BAUwAwEB/zANBgkq
hkiG9w0BAQsFAAOCAgEAh7yvPSX3qzWtczJNO4HGzo0xJC9vnEy01xKLOPZiGSFE
CFA15mtCnX1hYglkK8Bp7UnKMo9MwQFC4WLjBj7Ts6NamR0KpMf5M75WrCCA55UT
aWbwqFmHH47j7DYl/j1WK/nLocAzW3zyjDQaBArAls9Iw5nkeonyl+yaXh/7J45G
tNRrMyyxk1hl2C4NA3grQHycZiviNr6OQmgZ3sPexaPfAva3Zuwwv24UeliB0Lpb
opxcZJ9ojqSAok/eJCKSpywuVkxy61Iz2MKIpLA+WoRFjVGuvM5rZPSEQweWlnJT
f4GVKdfGQW9bzM27fMse/sg03z6odTn0rkxUM8TWsZR3Jg9YKbP2zgo4snU9FUMZ
RQA1A83U1T10yaeaCLBjN2psATQr7blYZhNUwYVr41C4K9+g3ghK3zhrKeaokBKQ
xo1aQZQNMyxrpe6NU+Iu9Esz4LRKaf8B4Q5vXJhf2YPqaz3FSHOFHNTiILvIEnuD
DFRwYLPkWlFLr5MYyjo8IlL/lcAjv3F3+Nx7qfvtIoLLxVON4hacYpG2uyyDGqg0
TiIvOLZ67W63nUk6h7+Pwm/8EhxTxFjguSOh0fu7GXtF75kDueBLoERr6DgcBTTg
adVnffnjz+hTFEjwXL48iGRPM142AGNOfXNp8tvPZOYjkc2prtIhGlvOu+De8tg=
-----END CERTIFICATE-----"""
    )
    tmp.flush()
    tmp.close()
    yield tmp.name
    os.unlink(tmp.name)


@pytest.fixture
def key_pem():
    """This is the key entry of a self-signed local cert"""
    # avoid PermissionError on Windows by deleting later
    tmp = NamedTemporaryFile('w', delete=False)
    tmp.write(
        """-----BEGIN ENCRYPTED PRIVATE KEY-----
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
xZ36Vrgc4hfaUiifsIiDwA==
-----END ENCRYPTED PRIVATE KEY-----"""
    )
    tmp.flush()
    tmp.close()
    yield tmp.name
    os.unlink(tmp.name)


@pytest.mark.parametrize('uses', ['HTTPGateway', 'WebSocketGateway'])
def test_uvicorn_ssl_deprecated(cert_pem, key_pem, uses):
    args = set_gateway_parser().parse_args(
        [
            '--uses',
            uses,
            '--uvicorn-kwargs',
            f'ssl_certfile: {cert_pem}',  # deprecated
            f'ssl_keyfile: {key_pem}',  # deprecated
            'ssl_keyfile_password: abcd',
        ]
    )
    with AsyncNewLoopRuntime(args, req_handler_cls=GatewayRequestHandler):
        pass


@pytest.mark.parametrize('uses', ['HTTPGateway', 'WebSocketGateway'])
def test_uvicorn_ssl(cert_pem, key_pem, uses):
    args = set_gateway_parser().parse_args(
        [
            '--uses',
            uses,
            '--uvicorn-kwargs',
            'ssl_keyfile_password: abcd',
            '--ssl-certfile',
            f'{cert_pem}',
            '--ssl-keyfile',
            f'{key_pem}',
        ]
    )
    with AsyncNewLoopRuntime(args, req_handler_cls=GatewayRequestHandler):
        pass


@pytest.mark.parametrize('uses', ['HTTPGateway', 'WebSocketGateway'])
def test_uvicorn_ssl_wrong_password(cert_pem, key_pem, uses):
    args = set_gateway_parser().parse_args(
        [
            '--uses',
            uses,
            '--uvicorn-kwargs',
            'ssl_keyfile_password: abcde',
            '--ssl-certfile ',
            f'{cert_pem}',
            '--ssl-keyfile ',
            f'{key_pem}',
        ]
    )
    with pytest.raises(ssl.SSLError):
        with AsyncNewLoopRuntime(args, req_handler_cls=GatewayRequestHandler):
            pass


@pytest.mark.parametrize('uses', ['HTTPGateway', 'WebSocketGateway'])
def test_uvicorn_ssl_wrong_password(cert_pem, key_pem, uses):
    args = set_gateway_parser().parse_args(
        [
            '--uses',
            uses,
            '--uvicorn-kwargs',
            'ssl_keyfile_password: abcde',
            '--ssl-certfile',
            f'{cert_pem}',
            '--ssl-keyfile',
            f'{key_pem}',
        ]
    )
    with pytest.raises(ssl.SSLError):
        with AsyncNewLoopRuntime(args, req_handler_cls=GatewayRequestHandler):
            pass


@pytest.mark.parametrize('protocol', ['http', 'websocket'])
def test_uvicorn_ssl_with_flow(cert_pem, key_pem, protocol, capsys, error_log_level):
    with Flow(
        protocol=protocol,
        uvicorn_kwargs=[
            'ssl_keyfile_password: abcd',
        ],
        ssl_certfile=cert_pem,
        ssl_keyfile=key_pem,
    ) as f:

        with pytest.raises(aiohttp.ClientConnectorCertificateError):
            Client(protocol=protocol, port=f.port, tls=True).index([Document()])


da = DocumentArray([Document(text='text_input')])


@pytest.mark.parametrize(
    'docs_input',
    [
        {'data': [{'text': 'text_input'}]},
        {'data': {'docs': [{'text': 'text_input'}]}},
        {'data': da.to_dict()},
        {'data': {'docs': da.to_dict()}},
        {'data': [da[0].to_dict()]},
        {'data': {'docs': [da[0].to_dict()]}},
    ],
)
def test_app_models_acceptance(docs_input):
    f = Flow(protocol='http').add()

    with f:
        r = req.post(f'http://localhost:{f.port}/index', json=docs_input)

    assert DocumentArray.from_dict(r.json()['data'])[0].text == 'text_input'


@pytest.fixture
def health_check_env():
    _prev_loglevel = os.environ.get('JINA_LOG_LEVEL', None)
    os.environ['JINA_LOG_LEVEL'] = 'INFO'
    os.environ['CICD_JINA_DISABLE_HEALTHCHECK_LOGS'] = '1'
    yield
    os.environ['JINA_LOG_LEVEL'] = _prev_loglevel
    os.environ.pop('CICD_JINA_DISABLE_HEALTHCHECK_LOGS')


@pytest.fixture
def no_health_check_env():
    _prev_loglevel = os.environ.get('JINA_LOG_LEVEL', None)
    os.environ['JINA_LOG_LEVEL'] = 'INFO'
    yield
    os.environ['JINA_LOG_LEVEL'] = _prev_loglevel


def test_healthcheck_logs_http(capfd, no_health_check_env):
    f = Flow(protocol='http', port=12345).add()
    with f:
        req.get('http://localhost:12345/')
        req.get('http://localhost:12345/docs')

    out, _ = capfd.readouterr()
    assert '"GET / HTTP/1.1" 200 OK' in out
    assert '"GET /docs HTTP/1.1" 200 OK' in out


def test_no_healthcheck_logs_http_with_env(capfd, health_check_env):
    f = Flow(protocol='http', port=12345).add()
    with f:
        req.get('http://localhost:12345/')
        req.get('http://localhost:12345/docs')

    out, _ = capfd.readouterr()
    assert '"GET / HTTP/1.1" 200 OK' not in out
    assert '"GET /docs HTTP/1.1" 200 OK' in out


def test_healthcheck_logs_websocket(capfd, no_health_check_env):
    f = Flow(protocol='websocket', port=12345).add()
    with f:
        req.get('http://localhost:12345/')
        f.post('/', inputs=DocumentArray.empty())

    out, _ = capfd.readouterr()
    assert '"GET / HTTP/1.1" 200 OK' in out


def test_healthcheck_logs_websocket_with_env(capfd, health_check_env):
    f = Flow(protocol='websocket', port=12345).add()
    with f:
        f.post('/', inputs=DocumentArray.empty())
        req.get('http://localhost:12345/')

    out, _ = capfd.readouterr()
    assert '"GET / HTTP/1.1" 200 OK' not in out
