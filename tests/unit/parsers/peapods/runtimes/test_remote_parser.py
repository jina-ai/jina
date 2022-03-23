import argparse

from jina.parsers.orchestrate.runtimes.remote import mixin_http_gateway_parser


def test_runtime_parser():
    parser = argparse.ArgumentParser(
        epilog=f'Test', description='Test Command Line Interface'
    )

    mixin_http_gateway_parser(parser)

    args = parser.parse_args([])
    assert args.uvicorn_kwargs is None

    args = parser.parse_args(['--uvicorn-kwargs', 'ssl_keyfile: /tmp/cert.pem'])
    assert args.uvicorn_kwargs == {'ssl_keyfile': '/tmp/cert.pem'}

    args = parser.parse_args(
        [
            '--uvicorn-kwargs',
            'ssl_keyfile: /tmp/cert.pem',
            'ssl_keyfile_password: 1234e',
        ]
    )
    assert args.uvicorn_kwargs == {
        'ssl_keyfile': '/tmp/cert.pem',
        'ssl_keyfile_password': '1234e',
    }
