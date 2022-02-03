import argparse
from jina.parsers.orchestrate.runtimes.container import mixin_container_runtime_parser


def test_runtime_parser():
    parser = argparse.ArgumentParser(
        epilog=f'Test', description='Test Command Line Interface'
    )

    mixin_container_runtime_parser(parser)

    args = parser.parse_args([])
    assert args.docker_kwargs is None

    args = parser.parse_args(['--docker-kwargs', 'hello: 0', 'bye: 1'])
    assert args.docker_kwargs == {'hello': 0, 'bye': 1}

    args = parser.parse_args(['--docker-kwargs', 'hello: "0"', 'bye: "1"'])
    assert args.docker_kwargs == {'hello': '0', 'bye': '1'}

    args = parser.parse_args(
        ['--docker-kwargs', 'environment: ["VAR1=BAR", "VAR2=FOO"]', 'hello: 0']
    )
    assert args.docker_kwargs == {'environment': ['VAR1=BAR', 'VAR2=FOO'], 'hello': 0}
