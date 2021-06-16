import argparse
import pytest
from jina.parsers.hubble.push import mixin_hub_push_parser


def test_push_parser():
    parser = argparse.ArgumentParser(
        epilog=f'Test', description='Test Hub Command Line Interface'
    )

    mixin_hub_push_parser(parser)

    args = parser.parse_args(['foo/'])
    assert args.path == 'foo/'
    assert args.public is False
    assert args.private is False
    assert args.force is None
    assert args.secret is None

    args = parser.parse_args(['foo/', '--public'])
    assert args.public is True
    assert args.private is False

    args = parser.parse_args(['foo/', '--private'])
    assert args.public is False
    assert args.private is True

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        args = parser.parse_args(['foo/', '--private', '--public'])
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 2

    args = parser.parse_args(['foo/', '--force', '8iag38yu', '--secret', '8iag38yu'])
    assert args.force == '8iag38yu'
    assert args.secret == '8iag38yu'
    assert args.public is False
    assert args.private is False
