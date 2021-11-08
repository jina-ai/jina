import argparse

import pytest

from jina.parsers.hubble.new import mixin_hub_new_parser


def test_new_parser():
    parser = argparse.ArgumentParser(
        epilog=f'Test', description='Test Hub Command Line Interface'
    )

    mixin_hub_new_parser(parser)

    args = parser.parse_args([])
    assert not args.add_dockerfile
    assert not args.advance_configuration
    assert args.name == None
    assert args.path == None
    assert args.description == None
    assert args.keywords == None
    assert args.url == None

    args = parser.parse_args(['--add-dockerfile'])
    assert args.add_dockerfile

    args = parser.parse_args(['--advance-configuration'])
    assert args.advance_configuration

    args = parser.parse_args(
        [
            '--name',
            'Dummy Executor',
            '--path',
            'Dummy Path',
            '--description',
            'Dummy description',
            '--keywords',
            'Dummy keywords',
            '--url',
            'Dummy url',
        ]
    )
    assert not args.add_dockerfile
    assert not args.advance_configuration
    assert args.name == 'Dummy Executor'
    assert args.path == 'Dummy Path'
    assert args.description == 'Dummy description'
    assert args.keywords == 'Dummy keywords'
    assert args.url == 'Dummy url'

    args = parser.parse_args(
        [
            '--name',
            'Dummy Executor',
            '--path',
            'Dummy Path',
            '--description',
            'Dummy description',
            '--keywords',
            'Dummy keywords',
            '--url',
            'Dummy url',
            '--advance-configuration',
        ]
    )
    assert not args.add_dockerfile
    assert args.advance_configuration
    assert args.name == 'Dummy Executor'
    assert args.path == 'Dummy Path'
    assert args.description == 'Dummy description'
    assert args.keywords == 'Dummy keywords'
    assert args.url == 'Dummy url'

    args = parser.parse_args(
        [
            '--add-dockerfile',
            '--name',
            'Dummy Executor',
            '--path',
            'Dummy Path',
            '--description',
            'Dummy description',
            '--keywords',
            'Dummy keywords',
            '--url',
            'Dummy url',
        ]
    )
    assert args.add_dockerfile
    assert not args.advance_configuration
    assert args.name == 'Dummy Executor'
    assert args.path == 'Dummy Path'
    assert args.description == 'Dummy description'
    assert args.keywords == 'Dummy keywords'
    assert args.url == 'Dummy url'
