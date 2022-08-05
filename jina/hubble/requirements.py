"""Module for helper functions for parsing requirements file."""

import os
import re
from typing import Dict, Tuple, cast, List
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
ENV_VAR_RE = re.compile(r"(?P<var>\$\{(?P<name>[A-Z0-9_]+)\})")

ENV_VAR_RE_ONLY_MATCH_UPPERCASE_UNDERLINE = re.compile(r"^[A-Z0-9_]+$");


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


def get_env_variables(line: str) -> List:
    """ 
    search the environment variable only match uppercase letter and number and the `_` (underscore).
    :param line: a line of a requirement file
    :return: a List of components
    """
    env_variables = [];
    for env_var, var_name in ENV_VAR_RE.findall(line):
        env_variables.append(var_name)
    env_variables = list(set(env_variables));
    return env_variables


def check_env_variable(env_variable: str) -> bool:
    """ 
    check the environment variables is limited
    to uppercase letter and number and the `_` (underscore).
    :param env_variable: env_variable in the requirements.txt file
    :return: True or False if not satisfied
    """
    return True if ENV_VAR_RE_ONLY_MATCH_UPPERCASE_UNDERLINE.match(env_variable) is not None else False


def expand_env_variables(line: str) -> str:
    """ 
    Replace all environment variables that can be retrieved via `os.getenv`.
    The only allowed format for environment variables defined in the
    requirement file is `${MY_VARIABLE_1}` to ensure two things:
    1. Strings that contain a `$` aren't accidentally (partially) expanded.
    2. Ensure consistency across platforms for requirement files.
    Valid characters in variable names follow the `POSIX standard
    <http://pubs.opengroup.org/onlinepubs/9699919799/>`_ and are limited
    to uppercase letter and number and the `_` (underscore).
    Replace environment variables in requirement if it's defined.
    :param line: a line of a requirement file
    :return: line
    """
    for env_var, var_name in ENV_VAR_RE.findall(line):
        value = os.getenv(var_name)
        if not value:
            raise Exception(f'The given requirements.txt require environment variables `{var_name}` does not exist!')
        line = line.replace(env_var, value)
    return line
