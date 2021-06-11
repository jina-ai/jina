import argparse
from jina.parsers.hubble.push import mixin_hub_push_parser


def test_push_parser():
    parser = argparse.ArgumentParser(
        epilog=f'Test', description='Test Hub Command Line Interface'
    )

    mixin_hub_push_parser(parser)

    args = parser.parse_args(['foo/'])
    assert args.path == 'foo/'
    assert args.public is True
    assert args.private is False

    args = parser.parse_args(['foo/', '--private'])
    assert args.private is True

    args = parser.parse_args(['foo/', '--private', '--force', '8iag38yu'])
    assert args.force == '8iag38yu'
