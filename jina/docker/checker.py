"""Module for validation functions."""
__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
import re
import tempfile
import unicodedata
from typing import Optional

from pkg_resources import resource_stream

from ..jaml import JAML

image_tag_regex = r'^hub.[a-zA-Z_$][a-zA-Z_\s\-\.$0-9]*$'
required = {'name', 'description'}
sver_regex = (
    r'^(=|>=|<=|=>|=<|>|<|!=|~|~>|\^)?(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)'
    r'\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)'
    r'(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+'
    r'(?:\.[0-9a-zA-Z-]+)*))?$'
)
name_regex = r'^[a-zA-Z_$][a-zA-Z_\s\-$0-9]{2,30}$'
excepts_regex = r'\b(error|failed|FAILURES)\b'


def check_registry(registry, name, repo_prefix) -> None:
    """
    Check registry image is valid within this registry.

    :param registry: the registry URL
    :param name: the name of the image
    :param repo_prefix: the prefix of the repo
    """
    if registry == 'https://index.docker.io/v1/' and not name.startswith(repo_prefix):
        raise ValueError(
            f'default registry only support image named with "{repo_prefix}", yours: {name}'
        )


def check_name(name) -> None:
    """
    Check the name is valid against the regex rule.

    :param name: the name
    """
    if not re.match(name_regex, name):
        raise ValueError(
            f'{name} is not a valid name, it should match with {name_regex}'
        )


def check_version(version) -> None:
    """
    Check the version against the regex.

    :param version: the version
    """
    if not re.match(sver_regex, version):
        raise ValueError(
            f'{version} is not a valid semantic version number, see http://semver.org/'
        )


def check_image_name(image_name) -> None:
    """
    Check the image name against the image tag regex.

    :param image_name: the name of the image
    """
    if not re.match(image_tag_regex, image_name):
        raise ValueError(
            f'{image_name} is not a valid image name for a Jina Hub image, it should match with {image_tag_regex}'
        )


def check_platform(platform_names) -> None:
    """
    Check the platform against the list of supported platforms.

    :param platform_names: the name of the platforms
    """
    with resource_stream(
        'jina', '/'.join(('resources', 'hub-builder', 'platforms.yml'))
    ) as fp:
        platforms = JAML.load(fp)

    for ss in platform_names:
        if ss not in platforms:
            raise ValueError(
                f'platform {ss} is not supported, should be one of {platforms}'
            )


def check_license(lic) -> str:
    """
    Check the license is a valid OS supported license.

    :param lic: the license
    :return: the full name of the license
    """
    with resource_stream(
        'jina', '/'.join(('resources', 'hub-builder', 'osi-approved.yml'))
    ) as fp:
        approved = JAML.load(fp)
    if lic not in approved:
        raise ValueError(f'license {lic} is not an OSI-approved license {approved}')
    return approved[lic]


def check_image_type(image_type) -> None:
    """
    Check the image type is valid.

    :param image_type: the type of image
    """
    allowed = {'pod', 'flow', 'app'}
    if image_type not in allowed:
        raise ValueError(
            f'type {image_type} is not allowed, should be one of {allowed}'
        )


def remove_control_characters(s) -> str:
    """
    Remove control characters.

    :param s: the string to check
    :return: the cleaned string
    """
    return ''.join(ch for ch in s if unicodedata.category(ch)[0] != 'C')


def safe_url_name(url) -> str:
    """
    Clean the url.

    :param url: the url input
    :return: the sanitized url
    """
    return url.lower().replace('_', '__').replace(' ', '_')


def get_exist_path(directory, filename) -> Optional[str]:
    """
    Check if path exists within the directory.

    :param directory: the directory within which to check
    :param filename: the filename which we check
    :return: if exists, the full path
    """
    r = os.path.join(directory, filename)
    if os.path.exists(r):
        return r


def get_summary_path(image_name: str) -> str:
    """
    Get full path to summary.

    :param image_name: the name of the image
    :return: the full path to the summary JSON file of the image
    """
    return os.path.join(
        tempfile.gettempdir(), image_name.replace('/', '_') + '_summary.json'
    )


def is_error_message(s) -> bool:
    """
    Check if the string matches an exception regex.

    :param s: the string to check
    :return: whether or not it matches
    """
    return re.search(excepts_regex, s, re.IGNORECASE | re.UNICODE) is not None
