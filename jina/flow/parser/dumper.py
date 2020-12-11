"""
# loader function format

    def dump_v_MAJOR[_MINOR](data)
    e.g.
        - def dump_v_1_1(data)
        - def dump_v_1(data)

# match priority
    if version is available:
        - dump_v_MAJOR_MINOR
        - dump_v_MAJOR
        - throw BadFlowYAMLVersion
    otherwise:
        - dump_v_legacy
"""

import argparse
from typing import Dict, Any

from .. import Flow
from ...parser import set_pod_parser


def _get_taboo():
    """Get a set of keys that should not be dumped"""
    return {k.dest for k in set_pod_parser()._actions if k.help == argparse.SUPPRESS}


def dump_v_legacy(data: 'Flow') -> Dict[str, Any]:
    r = {}
    if data._version:
        r['version'] = data._version

    if data._kwargs:
        r['with'] = data._kwargs

    if data._pod_nodes:
        r['pods'] = {}

    if 'gateway' in data._pod_nodes:
        # always dump gateway as the first pod, if exist
        r['pods']['gateway'] = {}

    for k, v in data._pod_nodes.items():
        if k == 'gateway':
            continue

        kwargs = {'needs': list(v.needs)} if v.needs else {}
        kwargs.update(v._kwargs)

        if 'name' in kwargs:
            kwargs.pop('name')

        r['pods'][k] = kwargs
    return r


def dump_v_1(data: 'Flow') -> Dict[str, Any]:
    r = {}
    if data._version:
        r['version'] = data._version

    if data._kwargs:
        r['with'] = data._kwargs

    if data._pod_nodes:
        r['pods'] = []

    last_name = 'gateway'
    for k, v in data._pod_nodes.items():
        if k == 'gateway':
            continue
        kwargs = {}
        # only add "needs" when the value is not the last pod name
        if list(v.needs) != [last_name]:
            kwargs = {'needs': list(v.needs)}
        kwargs.update(v._kwargs)
        for t in _get_taboo():
            if t in kwargs:
                kwargs.pop(t)
        last_name = kwargs['name']
        r['pods'].append(kwargs)
    return r
