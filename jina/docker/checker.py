__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
import re
import unicodedata

import tempfile
from pkg_resources import resource_stream

from ..jaml import JAML

image_tag_regex = r'^hub.[a-zA-Z_$][a-zA-Z_\s\-\.$0-9]*$'
required = {'name', 'description'}
sver_regex = r'^(=|>=|<=|=>|=<|>|<|!=|~|~>|\^)?(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)' \
             r'\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)' \
             r'(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+' \
             r'(?:\.[0-9a-zA-Z-]+)*))?$'
name_regex = r'^[a-zA-Z_$][a-zA-Z_\s\-$0-9]{2,30}$'
excepts_regex = r'\b(error|failed|FAILURES)\b'


def check_registry(registry, name, repo_prefix):
    if registry == 'https://index.docker.io/v1/' and not name.startswith(repo_prefix):
        raise ValueError(f'default registry only support image named with "{repo_prefix}", yours: {name}')


def check_name(s):
    if not re.match(name_regex, s):
        raise ValueError(f'{s} is not a valid name, it should match with {name_regex}')


def check_version(s):
    if not re.match(sver_regex, s):
        raise ValueError(f'{s} is not a valid semantic version number, see http://semver.org/')


def check_image_name(s):
    if not re.match(image_tag_regex, s):
        raise ValueError(f'{s} is not a valid image name for a Jina Hub image, it should match with {image_tag_regex}')


def check_platform(s):
    with resource_stream('jina', '/'.join(('resources', 'hub-builder', 'platforms.yml'))) as fp:
        platforms = JAML.load(fp)

    for ss in s:
        if ss not in platforms:
            raise ValueError(f'platform {ss} is not supported, should be one of {platforms}')


def check_license(s):
    with resource_stream('jina', '/'.join(('resources', 'hub-builder', 'osi-approved.yml'))) as fp:
        approved = JAML.load(fp)
    if s not in approved:
        raise ValueError(f'license {s} is not an OSI-approved license {approved}')
    return approved[s]


def check_image_type(s):
    allowed = {'pod', 'flow', 'app'}
    if s not in allowed:
        raise ValueError(f'type {s} is not allowed, should be one of {allowed}')


def remove_control_characters(s):
    return ''.join(ch for ch in s if unicodedata.category(ch)[0] != 'C')


def safe_url_name(s):
    return s.lower().replace('_', '__').replace(' ', '_')


def get_exist_path(directory, s):
    r = os.path.join(directory, s)
    if os.path.exists(r):
        return r


def get_summary_path(image_name: str):
    return os.path.join(tempfile.gettempdir(), image_name.replace('/', '_') + '_summary.json')


def is_error_message(s):
    return re.search(excepts_regex, s, re.IGNORECASE | re.UNICODE) is not None
