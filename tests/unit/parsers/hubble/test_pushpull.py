import argparse
import pytest
from jina.parsers.hubble.push import mixin_hub_push_parser
from jina.parsers.hubble.pull import mixin_hub_pull_parser


def test_push_parser(tmpdir):
    parser = argparse.ArgumentParser(
        epilog=f'Test', description='Test Hub Command Line Interface'
    )

    mixin_hub_push_parser(parser)
    tmpdir = str(tmpdir)

    args = parser.parse_args([tmpdir])
    assert args.path == tmpdir
    assert args.force_update is None
    assert args.secret is None
    assert not hasattr(args, 'public')
    assert not hasattr(args, 'private')

    args = parser.parse_args([tmpdir, '-t', 'v1', '-t', 'v2'])
    assert args.tag == ['v1', 'v2']

    args = parser.parse_args([tmpdir, '--tag', 'v1', '--tag', 'v2'])
    assert args.tag == ['v1', 'v2']

    args = parser.parse_args([tmpdir, '-f', 'Dockerfile'])
    assert args.dockerfile == 'Dockerfile'

    args = parser.parse_args([tmpdir, '--dockerfile', 'Dockerfile'])
    assert args.dockerfile == 'Dockerfile'

    args = parser.parse_args([tmpdir, '--public'])
    assert args.public is True
    assert not hasattr(args, 'private')

    args = parser.parse_args([tmpdir, '--private'])
    assert not hasattr(args, 'public')
    assert args.private is True

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        args = parser.parse_args([tmpdir, '--private', '--public'])
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 2

    args = parser.parse_args(
        [tmpdir, '--force-update', '8iag38yu', '--secret', '8iag38yu']
    )
    assert args.force_update == '8iag38yu'
    assert args.secret == '8iag38yu'
    assert not hasattr(args, 'public')
    assert not hasattr(args, 'private')


def test_pull_parser():
    parser = argparse.ArgumentParser(
        epilog=f'Test', description='Test Hub Command Line Interface'
    )

    mixin_hub_pull_parser(parser)

    args = parser.parse_args(['jinahub://dummy'])
    assert args.uri == 'jinahub://dummy'
