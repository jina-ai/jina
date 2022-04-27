"""Module for helper functions for parsing requirements file."""

import os
import re
from typing import Dict, Tuple, cast

from pkg_resources import Requirement

# Adopted from requirements-parser:
# https://github.com/madpah/requirements-parser

VCS = [
    'git',
    'hg',
    'svn',
    'bzr',
]

VCS_SCHEMES = [
    'git',
    'git+https',
    'git+ssh',
    'git+git',
    'hg+http',
    'hg+https',
    'hg+static-http',
    'hg+ssh',
    'svn',
    'svn+svn',
    'svn+http',
    'svn+https',
    'svn+ssh',
    'bzr+http',
    'bzr+https',
    'bzr+ssh',
    'bzr+sftp',
    'bzr+ftp',
    'bzr+lp',
]

URI_REGEX = re.compile(
    r'^(?P<scheme>https?|file|ftps?)://(?P<path>[^#]+)' r'(#(?P<fragment>\S+))?'
)

VCS_SCHEMES_REGEX = r'|'.join([scheme.replace('+', r'\+') for scheme in VCS_SCHEMES])
VCS_REGEX = re.compile(
    rf'^(?P<scheme>{VCS_SCHEMES_REGEX})://((?P<login>[^/@]+)@)?'
    r'(?P<path>[^#@]+)(@(?P<revision>[^#]+))?(#(?P<fragment>\S+))?'
)


extras_require_search = re.compile(r'(?P<name>.+)\[(?P<extras>[^\]]+)\]')


def _parse_fragment(fragment_string: str) -> Dict[str, str]:
    """Takes a fragment string nd returns a dict of the components

    :param fragment_string: a fragment string
    :return: a dict of components
    """
    fragment_string = fragment_string.lstrip('#')

    try:
        return dict(
            cast(Tuple[str, str], tuple(key_value_string.split('=')))
            for key_value_string in fragment_string.split('&')
        )
    except ValueError:
        raise ValueError(f'Invalid fragment string {fragment_string}')


def parse_requirement(line: str) -> 'Requirement':
    """Parses a Requirement from a line of a requirement file.

    :param line: a line of a requirement file
    :returns: a Requirement instance for the given line
    """

    vcs_match = VCS_REGEX.match(line)
    uri_match = URI_REGEX.match(line)

    if vcs_match is not None:
        groups = vcs_match.groupdict()
        name = os.path.basename(groups['path']).split('.')[0]
        egg = None
        if groups['fragment']:
            fragment = _parse_fragment(groups['fragment'])
            egg = fragment.get('egg')

        line = f'{egg or name} @ {line}'
    elif uri_match is not None:
        groups = uri_match.groupdict()
        name = os.path.basename(groups['path']).split('.')[0]
        egg = None
        if groups['fragment']:
            fragment = _parse_fragment(groups['fragment'])
            egg = fragment.get('egg')

        line = f'{egg or name} @ {line}'

    return Requirement.parse(line)
