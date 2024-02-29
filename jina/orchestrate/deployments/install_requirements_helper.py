import os
import re

from typing import TYPE_CHECKING, Tuple, Dict, Optional, cast
from pkg_resources import Requirement

if TYPE_CHECKING:  # pragma: no cover
    from pathlib import Path

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

ENV_VAR_RE_ONLY_MATCH_UPPERCASE_UNDERLINE = re.compile(r"^[A-Z0-9_]+$")

extras_require_search = re.compile(r'(?P<name>.+)\[(?P<extras>[^\]]+)\]')


def _parse_fragment(fragment_string: str) -> Dict[str, str]:
    """Takes a fragment string and returns a dict of the components

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


def _parse_requirement(line: str) -> 'Requirement':
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


def _expand_env_variables(line: str) -> str:
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
            raise Exception(
                f'The given requirements.txt require environment variables `{var_name}` does not exist!'
            )
        line = line.replace(env_var, value)
    return line


def _get_install_options(requirements_file: 'Path', excludes: Tuple[str] = ('jina',)):
    with requirements_file.open() as requirements:
        install_options = []
        install_reqs = []
        for req in requirements:
            req = req.strip()
            if (not req) or req.startswith('#'):
                continue
            elif req.startswith('-'):
                for index, item in enumerate(req.split(' ')):
                    install_options.append(_expand_env_variables(item))
            else:
                expand_req = _expand_env_variables(req)
                req_spec = _parse_requirement(expand_req)

                if req_spec.project_name not in excludes or len(req_spec.extras) > 0:
                    install_reqs.append(expand_req)
    return install_reqs, install_options


def _is_requirements_installed(requirements_file: 'Path') -> bool:
    """Return True if requirements.txt is installed locally
    :param requirements_file: the requirements.txt file
    :return: True or False if not satisfied
    """
    import pkg_resources
    from pkg_resources import (
        DistributionNotFound,
        RequirementParseError,
        VersionConflict,
    )

    install_reqs, install_options = _get_install_options(requirements_file)

    if len(install_reqs) == 0:
        return True

    try:
        pkg_resources.require('\n'.join(install_reqs))
    except (DistributionNotFound, VersionConflict, RequirementParseError) as ex:
        import warnings

        warnings.warn(repr(ex))
        return isinstance(ex, VersionConflict)
    return True


def _install_requirements(requirements_file: 'Path', timeout: int = 1000):
    """Install modules included in requirements file
    :param requirements_file: the requirements.txt file
    :param timeout: the socket timeout (default = 1000s)
    """
    import subprocess
    import sys

    if _is_requirements_installed(requirements_file):
        return

    install_reqs, install_options = _get_install_options(requirements_file)

    subprocess.check_call(
        [
            sys.executable,
            '-m',
            'pip',
            'install',
            '--compile',
            f'--default-timeout={timeout}',
        ]
        + install_reqs
        + install_options
    )


def install_package_dependencies(pkg_path: Optional['Path']) -> None:
    """

    :param pkg_path: package path
    """
    # install the dependencies included in requirements.txt
    if pkg_path:
        requirements_file = pkg_path / 'requirements.txt'

        if requirements_file.exists():
            _install_requirements(requirements_file)


def _get_package_path_from_uses(uses: str) -> Optional['Path']:
    if isinstance(uses, str) and os.path.exists(uses):
        from pathlib import Path

        return Path(os.path.dirname(os.path.abspath(uses)))
    else:
        from hubble.executor.helper import is_valid_huburi

        if not is_valid_huburi(uses):
            from jina.logging.predefined import default_logger

            default_logger.warning(
                f'Error getting the directory name from {uses}. `--install-requirements` option is only valid when `uses` is a configuration file.'
            )
        return None
